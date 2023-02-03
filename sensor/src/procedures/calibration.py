from datetime import datetime
import math
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
        self.active_mqtt_queue = utils.ActiveMQTTQueue()

    def run(self) -> None:
        calibration_time = datetime.utcnow().timestamp()

        # randomize calibration gas order
        result = custom_types.CalibrationProcedureData(
            gases=self.config.calibration.gases, readings=[]
        )

        # save the currently active valve input for later
        previous_measurement_valve_input = self.hardware_interface.valves.active_input

        # start the calibration sampling
        self.hardware_interface.co2_sensor.start_calibration_sampling()
        self.hardware_interface.co2_sensor.set_filter_setting(
            average=self.config.calibration.sampling.seconds_per_sample
        )

        for gas in self.config.calibration.gases:
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
            gas_readings: list[custom_types.CO2SensorData] = []
            for _ in range(self.config.calibration.sampling.sample_count):
                start_time = time.time()
                gas_readings.append(
                    self.hardware_interface.co2_sensor.get_current_concentration()
                )
                elapsed_time = time.time() - start_time
                remaining_loop_time = (
                    self.config.calibration.sampling.seconds_per_sample - elapsed_time
                )
                if remaining_loop_time > 0:
                    time.sleep(remaining_loop_time)

            result.readings.append(gas_readings)

        # start the calibration sampling, reset CO2 sensor to default filters
        self.hardware_interface.co2_sensor.stop_calibration_sampling()
        self.hardware_interface.co2_sensor.set_filter_setting()

        # send calibration result via mqtt
        self.active_mqtt_queue.enqueue_message(
            self.config,
            custom_types.MQTTDataMessageBody(
                revision=self.config.revision,
                timestamp=round(time.time(), 2),
                value=custom_types.MQTTCalibrationData(
                    variant="calibration", data=result
                ),
            ),
        )

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

        # skip calibration when sensor has had power for less than 30
        # minutes (a full warming up is required for maximum accuracy)
        seconds_since_last_co2_sensor_boot = (
            time.time() - self.hardware_interface.co2_sensor.last_powerup_time
        )
        if seconds_since_last_co2_sensor_boot < 1800:
            return False

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
