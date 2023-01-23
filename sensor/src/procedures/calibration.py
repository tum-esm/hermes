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
        reference_values: list[float] = []
        random.shuffle(calibration_gases)

        # save the currently active valve input for later
        previous_measurement_valve_input = self.hardware_interface.valves.active_input

        # start the calibration sampling
        self.hardware_interface.co2_sensor.start_calibration_sampling()
        self.hardware_interface.co2_sensor.set_filter_setting(
            average=self.config.calibration.sampling.seconds_per_sample
        )

        for gas in calibration_gases:
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
            for _ in range(self.config.calibration.sampling.sample_count):
                sampling_data.append(
                    self.hardware_interface.co2_sensor.get_current_concentration()
                )
                # TODO: is this how  the average filter works or do we need time.sleep() as well
            reference_values.append(
                sum([d.raw for d in sampling_data]) / len(sampling_data)
            )

        # start the calibration sampling, reset CO2 sensor to default filters
        self.hardware_interface.co2_sensor.stop_calibration_sampling()
        self.hardware_interface.co2_sensor.set_filter_setting()

        # send correction values to sensor
        # TODO: send LCI data to CO2 sensor

        # TODO: after all gases, check with the last gas again?

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
        current_utc_timestamp = datetime.utcnow().timestamp()

        # TODO: skip calibration when sensor has had power for
        # less than 30 minutes -> a full warming up is required
        # for maximum accuracy

        # if last calibration time is unknown, calibrate now
        # should only happen when the state.json is not copied
        # during the upgrade routine or its interface changes
        if state.last_calibration_time is None:
            return True

        seconds_per_calibration_interval = (
            3600 * self.config.calibration.hours_between_calibrations
        )
        last_calibration_due_time = (
            math.floor(current_utc_timestamp / seconds_per_calibration_interval)
            * seconds_per_calibration_interval
        )

        return state.last_calibration_time < last_calibration_due_time
