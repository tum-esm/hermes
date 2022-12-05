# TODO: Put 50 meter pipe at every inlet. Still configurable.

# class last_measurement_value = datetime.now()

import time
from typing import Literal
from src import custom_types, utils, interfaces


class MeasurementProcedure:
    """
    runs every mainloop call when no configuration or calibration ran

    1. Check whether the wind and co2 sensor report any issues
    2. Check wind sensor direction and possibly change inlet
    3. Apply calibration using SHT 21 values
    4. Do 2 minutes of measurements
    """

    def __init__(self, config: custom_types.Config) -> None:
        self.logger = utils.Logger(config, origin="measurements")
        self.config = config

        self.wind_sensor_interface = interfaces.WindSensorInterface(config)
        self.valve_interfaces = interfaces.ValveInterface(config)
        self.pump_interface = interfaces.PumpInterface(config)
        self.active_valve_number: Literal[1, 2, 3, 4] | None = None

        self.input_air_sensor = interfaces.InputAirSensorInterface()

        self.co2_sensor_interface = interfaces.CO2SensorInterface(config)
        self.last_measurement_time: float = 0

    def _switch_to_valve_number(self, new_valve_number: Literal[1, 2, 3, 4]) -> None:
        self.valve_interfaces.set_active_input(new_valve_number)
        self.pump_interface.run(desired_rps=30, duration=20)
        self.active_valve_number = new_valve_number
        # TODO: measure airflow and calculate rounds that need
        #       to be pumped for 50 meters of pipe

    def _get_current_wind_data(self) -> custom_types.WindSensorData:
        # fetch wind data
        while True:
            wind_data = self.wind_sensor_interface.get_current_wind_measurement()
            if wind_data is not None:
                return wind_data
            self.logger.debug("no current wind data, waiting 2 seconds")
            time.sleep(2)

        # TODO: Add timeout error

    def _update_input_valve(self) -> None:
        """
        1. fetches the current wind data from the wind sensor
        2. calculates which air inlet direction is the closest one
        3. possibly performs the switch between air inlets
        """

        # fetch wind data
        wind_data = self._get_current_wind_data()

        # determine new valve
        new_valve = min(
            self.config.valves.air_inlets,
            key=lambda x: utils.math.distance_between_angles(
                x.direction, wind_data.direction_avg
            ),
        )

        # perform switch
        if self.active_valve_number is None:
            self.logger.info(f"enabeling to air inlet {new_valve}")
            self._switch_to_valve_number(new_valve.number)
        else:
            if self.active_valve_number != new_valve.number:
                if wind_data.speed_avg < 0.2:
                    self.logger.debug(
                        f"wind speed very low ({wind_data.speed_avg} m/s)"
                    )
                    self.logger.info(f"staying at air inlet {new_valve}")
                else:
                    self.logger.info(f"switching to air inlet {new_valve}")
                    self._switch_to_valve_number(new_valve.number)
            else:
                self.logger.info(f"staying at air inlet {new_valve}")

    def _update_input_air_calibration(self) -> None:
        _, humidity = self.input_air_sensor.get_current_values()
        self.co2_sensor_interface.set_calibration_values(humidity=humidity)
        if humidity is None:
            self.logger.warning("could not read humidity value from SHT21")

    def run(self) -> None:
        start_time = time.time()

        # check whether the sensors report any errors
        self.co2_sensor_interface.check_sensor_errors()
        self.wind_sensor_interface.check_sensor_errors()
        # TODO: implement shut down and retry logic (if error
        #       happens 3 times in a row, report)

        # switch to up-to-date valve every two minutes
        self._update_input_valve()

        # run the pump for the whole procedure
        self.pump_interface.set_desired_pump_rps(20)
        time.sleep(1)

        self._update_input_air_calibration()

        # do regular measurements for about 2 minutes
        while True:
            now = time.time()
            if now - start_time > 120:
                break

            time_since_last_measurement = now - self.last_measurement_time
            if time_since_last_measurement < 5:
                time.sleep(5 - time_since_last_measurement)
            self.last_measurement_time = now

            current_sensor_data = self.co2_sensor_interface.get_current_concentration()
            self.logger.info(f"new measurement: {current_sensor_data}")

            # TODO: write out measurements to data files
            # TODO: write out measurements to mqtt broker

        self.pump_interface.set_desired_pump_rps(0)
