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

        # state variables
        self.last_measurement_time: float = 0
        self.message_queue = utils.MessageQueue()
        self.rb_pressure = utils.RingBuffer(
            self.config.calibration.average_air_inlet_measurements
        )
        self.rb_humidity = utils.RingBuffer(
            self.config.calibration.average_air_inlet_measurements
        )

    def _update_air_inlet_parameters(self) -> None:
        """
        fetches the latest temperature and pressure data at air inlet
        """

        self.air_inlet_bme280_data = (
            self.hardware_interface.air_inlet_bme280_sensor.get_data()
        )

        # Add to ring buffer to calculate moving average of low cost sensor
        self.rb_pressure.append(self.air_inlet_bme280_data.pressure)

        self.air_inlet_sht45_data = (
            self.hardware_interface.air_inlet_sht45_sensor.get_data()
        )

        # Add to ring buffer to calculate moving average of low cost sensor
        self.rb_humidity.append(self.air_inlet_sht45_data.humidity)

    def _alternate_bottle_for_drying(self) -> None:
        """1. sets time for drying the air chamber with first calibration bottle
        2. switches order of calibration bottles every other day"""

        # set time extension for first bottle
        self.seconds_drying_with_first_bottle = (
            self.config.calibration.sampling_per_cylinder_seconds
        )

        # alternate order every other day
        days_since_unix = (datetime.now().date() - datetime(1970, 1, 1).date()).days
        alternate_order = days_since_unix % 2 == 1

        if alternate_order:
            self.sequence_calibration_bottle = self.config.calibration.gas_cylinders[
                ::-1
            ]
        else:
            self.sequence_calibration_bottle = self.config.calibration.gas_cylinders

    def run(self) -> None:
        state = utils.StateInterface.read()
        calibration_time = datetime.utcnow().timestamp()
        self.logger.info(
            f"starting calibration procedure at timestamp {calibration_time}",
            config=self.config,
        )

        # log the current CO2 sensor device info
        self.logger.info(
            f"GMP343 Sensor Info: {self.hardware_interface.co2_sensor.get_param_info()}"
        )

        # clear ring buffers
        self.rb_humidity.clear()
        self.rb_pressure.clear()

        # alternate calibration bottle order every other day
        # first bottle receives additional time to dry air chamber
        self._alternate_bottle_for_drying()

        for gas in self.sequence_calibration_bottle:
            # switch to each calibration valve
            self.hardware_interface.valves.set_active_input(gas.valve_number)
            calibration_procedure_start_time = time.time()

            while True:
                # idle until next measurement period
                seconds_to_wait_for_next_measurement = max(
                    self.config.measurement.sensor_frequency_seconds
                    - (time.time() - self.last_measurement_time),
                    0,
                )
                self.logger.debug(
                    f"sleeping {round(seconds_to_wait_for_next_measurement, 3)} seconds"
                )
                time.sleep(seconds_to_wait_for_next_measurement)
                self.last_measurement_time = time.time()

                # update air inlet parameters
                self._update_air_inlet_parameters()

                # perform a CO2 measurement
                current_sensor_data = (
                    self.hardware_interface.co2_sensor.get_current_concentration(
                        pressure=self.rb_pressure.avg(),
                        humidity=self.rb_humidity.avg(),
                    )
                )
                self.logger.debug(f"new calibration measurement: {current_sensor_data}")

                # send out MQTT measurement message
                self.message_queue.enqueue_message(
                    self.config,
                    custom_types.MQTTMeasurementMessageBody(
                        revision=state.current_config_revision,
                        timestamp=round(time.time(), 2),
                        value=custom_types.MQTTCalibrationData(
                            cal_bottle_id=float(gas.bottle_id),
                            cal_gmp343_raw=current_sensor_data.raw,
                            cal_gmp343_compensated=current_sensor_data.compensated,
                            cal_gmp343_filtered=current_sensor_data.filtered,
                            cal_bme280_temperature=self.air_inlet_bme280_data.temperature,
                            cal_bme280_humidity=self.air_inlet_bme280_data.humidity,
                            cal_bme280_pressure=self.air_inlet_bme280_data.pressure,
                            cal_sht45_temperature=self.air_inlet_sht45_data.temperature,
                            cal_sht45_humidity=self.air_inlet_sht45_data.humidity,
                            cal_gmp343_temperature=current_sensor_data.temperature,
                        ),
                    ),
                )

                if (
                    (self.last_measurement_time - calibration_procedure_start_time)
                    >= self.config.calibration.sampling_per_cylinder_seconds
                    + self.seconds_drying_with_first_bottle
                ):
                    break

            # reset drying time extension for following bottles
            self.seconds_drying_with_first_bottle = 0

        # switch back to measurement inlet
        self.hardware_interface.valves.set_active_input(
            self.config.measurement.air_inlets[0].valve_number
        )

        # flush the system after calibration at max pump speed
        self.hardware_interface.pump.flush_system(
            duration=self.config.calibration.system_flushing_seconds
        )

        # save last calibration time
        self.logger.debug("finished calibration: updating state")
        state = utils.StateInterface.read()
        state.last_calibration_time = calibration_time
        utils.StateInterface.write(state)

    def is_due(self) -> bool:
        """returns true when calibration procedure should run now"""

        # load state, kept during configuration procedures
        state = utils.StateInterface.read()
        current_utc_timestamp = datetime.utcnow().timestamp()

        # if last calibration time is unknown, calibrate now
        # should only happen when the state.json is not copied
        # during the upgrade routine or its interface changes
        if state.last_calibration_time is None:
            self.logger.info("last calibration time is unknown, calibrating now")
            return True

        seconds_between_calibrations = (
            3600 * self.config.calibration.calibration_frequency_hours
        )
        calibrations_since_start_time = math.floor(
            (current_utc_timestamp - self.config.calibration.start_timestamp)
            / seconds_between_calibrations
        )
        last_calibration_time = (
            calibrations_since_start_time * seconds_between_calibrations
            + self.config.calibration.start_timestamp
        )

        if state.last_calibration_time > last_calibration_time:
            self.logger.info("last calibration is up to date")
            return False

        # skip calibration when sensor has had power for less than 30
        # minutes (a full warming up is required for maximum accuracy)
        seconds_since_last_co2_sensor_boot = round(
            time.time() - self.hardware_interface.co2_sensor.last_powerup_time, 2
        )
        if seconds_since_last_co2_sensor_boot < 1800:
            self.logger.info(
                f"skipping calibration, sensor is still warming up (co2 sensor"
                + f" booted {seconds_since_last_co2_sensor_boot} seconds ago)"
            )
            return False

        self.logger.info(
            "last calibration is older than last calibration due date, calibrating now"
        )
        return True
