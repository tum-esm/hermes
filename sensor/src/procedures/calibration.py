from datetime import datetime
import math
import random
import time
from src import custom_types, utils, hardware


class CalibrationProcedure:
    """runs when a calibration is due"""

    def __init__(
        self,
        config: custom_types.Config,
        hardware_interface: hardware.HardwareInterface,
    ) -> None:
        self.logger, self.config = utils.Logger(origin="calibration-procedure"), config
        self.hardware_interface = hardware_interface

    def run(self) -> None:
        calibration_time = datetime.utcnow().timestamp()

        # randomize calibration gas order
        calibration_gases = self.config.calibration.gases.copy()
        random.shuffle(calibration_gases)

        previous_measurement_valve_input = self.hardware_interface.valves.active_input

        for gas in calibration_gases:
            self.hardware_interface.co2_sensor.start_calibration_sampling()
            self.hardware_interface.valves.set_active_input(gas.valve_number)

            # flush tube with calibration gas
            self.hardware_interface.pump.set_desired_pump_speed(
                unit="litres_per_minute",
                value=self.config.calibration.flushing.pumped_litres_per_minute,
            )
            time.sleep(self.config.calibration.flushing.seconds)

            # sample measurements and average them
            self.hardware_interface.pump.set_desired_pump_speed(
                unit="litres_per_minute",
                value=self.config.calibration.sampling.pumped_litres_per_minute,
            )
            sampling_data: list[custom_types.CO2SensorData] = []
            # TODO: perform sampling
            # TODO: perform averaging

            # send correction values to sensor
            self.hardware_interface.co2_sensor.stop_calibration_sampling()
            # TODO: send LCI data to CO2 sensor

        # FIXME: after all gases, check with the last gas again?

        # clean up tube again
        self.hardware_interface.valves.set_active_input(
            previous_measurement_valve_input
        )
        self.hardware_interface.pump.set_desired_pump_speed(
            unit="litres_per_minute",
            value=self.config.calibration.cleaning.pumped_litres_per_minute,
        )
        time.sleep(self.config.calibration.cleaning.seconds)

        # save last calibration time
        state = utils.StateInterface.read()
        state.last_calibration_time = calibration_time
        utils.StateInterface.write(state)

    def is_due(self) -> bool:
        """returns true when calibration procedure should run now"""

        # load state, kept during configuration procedures
        state = utils.StateInterface.read()

        # if last calibration time is unknown, calibrate now
        # should only happen when the state.json is not copied
        # during the upgrade routine or its interface changes
        if state.last_calibration_time is None:
            return True

        seconds_per_calibration_interval = (
            3600 * self.config.calibration.hours_between_calibrations
        )
        current_utc_timestamp = datetime.utcnow().timestamp()
        last_calibration_due_time = (
            math.floor(current_utc_timestamp / seconds_per_calibration_interval)
            * seconds_per_calibration_interval
        )

        return state.last_calibration_time < last_calibration_due_time
