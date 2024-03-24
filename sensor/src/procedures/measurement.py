import time
from typing import Optional, Literal

from src import custom_types, utils, hardware


class WindMeasurementProcedure:
    """runs every mainloop call after possible configuration/calibration

    1. Perform measurements for wind sensor
    2. Send out measurement data over MQTT"""

    def __init__(
        self,
        config: custom_types.Config,
        hardware_interface: hardware.HardwareInterface,
        simulate: bool = False,
    ) -> None:
        self.logger, self.config = utils.Logger(origin="measurement-procedure"), config
        self.hardware_interface = hardware_interface
        self.simulate = simulate

        # state variables
        self.wind_data: Optional[custom_types.WindSensorData] = None
        self.message_queue = utils.MessageQueue()

    def _read_latest_wind_sensor_communication(self) -> None:
        # wind measurement
        (
            self.wind_data,
            self.device_info,
        ) = self.hardware_interface.wind_sensor.get_current_sensor_measurement()

    def _send_latest_wind_sensor_communication(self) -> None:
        """
        fetches the latest wind data and sends it our over MQTT.
        """
        # send latest wind measurement info
        if self.wind_data is not None:
            self.logger.info(f"latest wind sensor measurement: {self.wind_data}")

            state = utils.StateInterface.read()

            self.message_queue.enqueue_message(
                self.config,
                custom_types.MQTTMeasurementMessageBody(
                    revision=state.current_config_revision,
                    timestamp=round(time.time(), 2),
                    value=custom_types.MQTTWindData(
                        wxt532_direction_min=self.wind_data.direction_min,
                        wxt532_direction_avg=self.wind_data.direction_avg,
                        wxt532_direction_max=self.wind_data.direction_max,
                        wxt532_speed_min=self.wind_data.speed_min,
                        wxt532_speed_avg=self.wind_data.speed_avg,
                        wxt532_speed_max=self.wind_data.speed_max,
                        wxt532_last_update_time=self.wind_data.last_update_time,
                    ),
                ),
            )
        else:
            self.logger.info(f"did not receive any wind sensor measurement")

        # send latest wind sensor device info
        if self.device_info is not None:
            self.logger.info(f"latest wind sensor device info: {self.device_info}")

            state = utils.StateInterface.read()

            self.message_queue.enqueue_message(
                self.config,
                custom_types.MQTTMeasurementMessageBody(
                    revision=state.current_config_revision,
                    timestamp=round(time.time(), 2),
                    value=custom_types.MQTTWindSensorInfo(
                        wxt532_temperature=self.device_info.temperature,
                        wxt532_heating_voltage=self.device_info.heating_voltage,
                        wxt532_supply_voltage=self.device_info.supply_voltage,
                        wxt532_reference_voltage=self.device_info.reference_voltage,
                        wxt532_last_update_time=self.device_info.last_update_time,
                    ),
                ),
            )
        else:
            self.logger.info(f"did not receive any wind sensor device info")

    def run(self) -> None:
        """
        1. collect and send wind measurements in 2m interval
        2. collect and send CO2 measurements in 10s intervals
        """
        self.logger.info(f"reading latest wind measurement")

        # Read wind data
        self._read_latest_wind_sensor_communication()

        # Send wind data
        self._send_latest_wind_sensor_communication()

        self.logger.info(f"finished reading latest wind measurement")


class CO2MeasurementProcedure:
    """runs every mainloop call after possible configuration/calibration

    1. Request latest GMP343 device info
    2. Collect latest pressure and humidity inlet sensor readings
    3. Update compensation values for CO2 sensor
    4. Perform measurements for CO2 sensor
    5. Send out measurement data over MQTT"""

    def __init__(
        self,
        config: custom_types.Config,
        hardware_interface: hardware.HardwareInterface,
        simulate: bool = False,
    ) -> None:
        self.logger, self.config = utils.Logger(origin="measurement-procedure"), config
        self.hardware_interface = hardware_interface
        self.simulate = simulate

        # state variables
        self.active_air_inlet: Optional[Literal[1, 2, 3, 4]] = None
        self.last_measurement_time: float = 0
        self.message_queue = utils.MessageQueue()
        self.rb_pressure = utils.RingBuffer(
            self.config.measurement.average_air_inlet_measurements
        )
        self.rb_humidity = utils.RingBuffer(
            self.config.measurement.average_air_inlet_measurements
        )

    def _update_air_inlet_parameters(self) -> None:
        """
        fetches the latest temperature and pressure data at air inlet
        """

        self.air_inlet_bme280_data = (
            self.hardware_interface.air_inlet_bme280_sensor.get_data()
        )

        # Add to ring buffer to calculate moving average of low-cost sensor
        self.rb_pressure.append(self.air_inlet_bme280_data.pressure)

        self.air_inlet_sht45_data = (
            self.hardware_interface.air_inlet_sht45_sensor.get_data()
        )

        # Add to ring buffer to calculate moving average of low-cost sensor
        self.rb_humidity.append(self.air_inlet_sht45_data.humidity)

    def run(self) -> None:
        """
        1. collect and send CO2 measurements in 10s intervals for 2 minutes
        """
        self.logger.info(
            f"starting {self.config.measurement.procedure_seconds} seconds long CO2 measurement interval"
        )
        measurement_procedure_start_time = time.time()

        # log the current CO2 sensor device info
        self.logger.info(
            f"GMP343 Sensor Info: {self.hardware_interface.co2_sensor.get_param_info()}"
        )

        # do regular measurements for about 2 minutes
        while True:
            state = utils.StateInterface.read()
            # idle until next measurement period
            seconds_to_wait_for_next_measurement = max(
                self.config.hardware.gmp343_filter_seconds_averaging
                - (time.time() - self.last_measurement_time),
                0,
            )
            self.logger.debug(
                f"sleeping {round(seconds_to_wait_for_next_measurement, 3)} seconds"
            )
            time.sleep(seconds_to_wait_for_next_measurement)
            self.last_measurement_time = time.time()

            # Get latest auxiliary sensor data information
            self._update_air_inlet_parameters()

            # perform a CO2 measurement
            current_sensor_data = (
                self.hardware_interface.co2_sensor.get_current_concentration(
                    pressure=self.rb_pressure.avg(),
                    humidity=self.rb_humidity.avg(),
                )
            )
            self.logger.debug(f"new measurement: {current_sensor_data}")

            # send out MQTT measurement message
            self.message_queue.enqueue_message(
                self.config,
                custom_types.MQTTMeasurementMessageBody(
                    revision=state.current_config_revision,
                    timestamp=round(time.time(), 2),
                    value=custom_types.MQTTMeasurementData(
                        gmp343_raw=current_sensor_data.raw,
                        gmp343_compensated=current_sensor_data.compensated,
                        gmp343_filtered=current_sensor_data.filtered,
                        gmp343_temperature=current_sensor_data.temperature,
                        bme280_temperature=self.air_inlet_bme280_data.temperature,
                        bme280_humidity=self.air_inlet_bme280_data.humidity,
                        bme280_pressure=self.air_inlet_bme280_data.pressure,
                        sht45_temperature=self.air_inlet_sht45_data.temperature,
                        sht45_humidity=self.air_inlet_sht45_data.humidity,
                    ),
                ),
            )

            # stop loop after defined measurement interval
            if (
                self.last_measurement_time - measurement_procedure_start_time
            ) >= self.config.measurement.procedure_seconds:
                break

        self.logger.info(f"finished CO2 measurement interval")
