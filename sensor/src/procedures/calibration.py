from datetime import datetime
import json
import math
import time
from typing import Generator
from src import custom_types, utils, hardware


def _ensure_section_duration(duration: float) -> Generator[None, None, None]:
    """Make sure that the duration of the section is at least
    the given duration.

    Usage:

    ```python
    # do one measurement every 6 seconds
    with ensure_section_duration(6):
        do_measurement()
    ```
    """

    start_time = time.time()
    yield
    remaining_loop_time = start_time + duration - time.time()
    if remaining_loop_time > 0:
        time.sleep(remaining_loop_time)


class CalibrationProcedure:
    """runs when a calibration is due"""

    def __init__(
        self,
        config: custom_types.Config,
        hardware_interface: hardware.HardwareInterface,
        testing: bool = False,
    ) -> None:
        self.logger = utils.Logger(
            origin="calibration-procedure", print_to_console=testing
        )
        self.config = config
        self.hardware_interface = hardware_interface
        self.active_mqtt_queue = utils.ActiveMQTTQueue()

    def run(self) -> None:
        self.logger.info(
            f"running calibration procedure at timestamp {calibration_time}"
        )
        calibration_time = datetime.utcnow().timestamp()
        result = custom_types.CalibrationProcedureData(
            gases=self.config.calibration.gases, readings=[], timestamps=[]
        )
        previous_measurement_valve_input = self.hardware_interface.valves.active_input

        self.logger.debug("setting the CO2 sensor to calibration mode")
        self.hardware_interface.co2_sensor.start_calibration_sampling()
        self.hardware_interface.co2_sensor.set_filter_setting(average=5)
        self.hardware_interface.pump.set_desired_pump_speed(
            unit="litres_per_minute", value=0.5
        )

        for gas in self.config.calibration.gases:
            self.hardware_interface.valves.set_active_input(gas.valve_number)

            gas_readings: list[custom_types.CO2SensorData] = []
            timestamps: list[float] = []
            number_of_readings = math.ceil(
                self.config.calibration.seconds_per_gas_bottle / 6
            )
            for _ in range(number_of_readings):
                with _ensure_section_duration(6):
                    timestamps.append(datetime.utcnow().timestamp())
                    gas_readings.append(
                        self.hardware_interface.co2_sensor.get_current_concentration()
                    )

            result.readings.append(gas_readings)
            result.timestamps.append(gas_readings)

        # start the calibration sampling, reset CO2 sensor to default filters
        self.hardware_interface.co2_sensor.stop_calibration_sampling()
        self.hardware_interface.co2_sensor.set_filter_setting()

        # clean up tube again
        self.hardware_interface.valves.set_active_input(
            previous_measurement_valve_input
        )

        # send calibration result via mqtt
        if self.testing:
            self.logger.info(
                f"calibration result is available",
                details=json.dumps(result.dict()),
            )
        else:
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

        # save last calibration time
        state = utils.StateInterface.read()
        state.last_calibration_time = calibration_time
        utils.StateInterface.write(state)

    # TODO: log more
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
