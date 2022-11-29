# TODO: Put 50 meter pipe at every inlet. Still configurable.

# class last_measurement_value = datetime.now()

import time
from typing import Literal
from src import types, utils, interfaces


def distance_between_angles(angle_1: float, angle_2: float) -> float:
    """calculate the directional distance (in degrees) between two angles"""
    if angle_1 > angle_2:
        return min(angle_1 - angle_2, 360 - (angle_1 - angle_2))
    else:
        return min(angle_2 - angle_1, 360 - (angle_2 - angle_1))


class MeasurementProcedure:
    """
    runs every mainloop call when no configuration or calibration ran

    1. Check wind sensor direction every x seconds
    2. If wind direction has changed, pump according to pipe length
    3. Check SHT 21 value every x seconds or on inlet change
    4. Apply calibration on SHT 21 value changes
    5. Do measurements
    """

    def __init__(self, config: types.Config) -> None:
        self.logger = utils.Logger(config, origin="measurements")
        self.config = config
        self.wind_sensor = interfaces.WindSensorInterface(config)
        self.valve_interfaces = interfaces.ValveInterface(config)
        self.pump_interface = interfaces.PumpInterface(config)
        self.active_valve_number: Literal[1, 2, 3, 4] | None = None

    def _switch_to_valve_number(self, new_valve_number: Literal[1, 2, 3, 4]) -> None:
        self.valve_interfaces.set_active_input(new_valve_number)
        self.pump_interface.run(desired_rps=30, duration=20)
        self.active_valve_number = new_valve_number
        # TODO: measure airflow and calculate rounds that need
        #       to be pumped for 50 meters of pipe

    def _update_input_valve(self) -> None:
        """
        1. fetches the current wind data from the wind sensor
        2. calculates which air inlet direction is the closest one
        3. possibly performs the switch between air inlets
        """

        # fetch wind data
        wind_data = None
        while True:
            wind_data = self.wind_sensor.get_current_wind_measurement()
            if wind_data is not None:
                break
            self.logger.debug("no current wind data, waiting 2 seconds")
            time.sleep(2)

        # determine new valve
        new_valve = min(
            self.config.valves.air_inlets,
            key=lambda x: distance_between_angles(x.direction, wind_data.direction_avg),
        )

        # perform switch
        if self.active_valve_number is None:
            self.logger.info(f"enabeling to air inlet {new_valve}")
            self._switch_to_valve_number(new_valve.number)
        else:
            if self.active_valve_number != new_valve.number:
                if wind_data.speed_avg < 0.2:
                    self.logger.debug(f"wind speed very low ({wind_data.speed_avg} m/s)")
                    self.logger.info(f"staying at air inlet {new_valve}")
                else:
                    self.logger.info(f"switching to air inlet {new_valve}")
                    self._switch_to_valve_number(new_valve.number)
            else:
                self.logger.info(f"staying at air inlet {new_valve}")

    def run(self, config: types.Config) -> None:
        self.logger.update_config(config)
        self.config = config

        self._update_input_valve_for_wind_data()

        # TODO: implement measurement procedure
