import time
from typing import Optional
from src import custom_types, utils, hardware


class MeasurementProcedure:
    """runs every mainloop call after possible configuration/calibration

    1. Check whether the wind and CO2 sensor report any issues
    2. Collect latest pressure and humidity inlet sensor readings
    3. Update compensation values for CO2 sensor
    4. Perform measurements for wind/CO2 sensor
    5. Send out measurement data over MQTT"""

    def __init__(
        self,
        config: custom_types.Config,
        hardware_interface: hardware.HardwareInterface,
    ) -> None:
        self.logger, self.config = utils.Logger(origin="measurement-procedure"), config
        self.hardware_interface = hardware_interface

        # state variables
        self.active_air_inlet: Optional[custom_types.MeasurementAirInletConfig] = None
        self.last_measurement_time: float = 0
        self.message_queue = utils.MessageQueue()

    def _update_air_inlet_parameters(self) -> None:
        """
        fetches the latest temperature and pressure data at air inlet
        """

        self.air_inlet_bme280_data = (
            self.hardware_interface.air_inlet_bme280_sensor.get_data()
        )
        self.air_inlet_sht45_data = (
            self.hardware_interface.air_inlet_sht45_sensor.get_data()
        )

    def _send_latest_wind_data(self) -> None:
        """
        fetches the latest wind data and sends it our over MQTT.
        """
        # wind measurement
        wind_data = self.hardware_interface.wind_sensor.get_current_wind_measurement()

        # determine new valve
        if wind_data is not None:
            self.logger.info(f"sending latest wind data: {wind_data}")

            state = utils.StateInterface.read()
            self.message_queue.enqueue_message(
                self.config,
                custom_types.MQTTMeasurementMessageBody(
                    revision=state.current_config_revision,
                    timestamp=round(time.time(), 2),
                    value=custom_types.MQTTWindData(
                        wxt532_direction_min=wind_data.direction_min,
                        wxt532_direction_avg=wind_data.direction_avg,
                        wxt532_direction_max=wind_data.direction_max,
                        wxt532_speed_min=wind_data.speed_min,
                        wxt532_speed_avg=wind_data.speed_avg,
                        wxt532_speed_max=wind_data.speed_max,
                        wxt532_last_update_time=wind_data.last_update_time,
                    ),
                ),
            )

    def run(self) -> None:
        """
        1. collect and send wind measurements in 2m intervals
        2. collect and send CO2 measurements in 10s intervals
        """
        self.logger.info(f"starting 2 minute measurement interval")
        measurement_procedure_start_time = time.time()

        # Send wind data
        self._send_latest_wind_data()

        # do regular measurements for about 2 minutes
        while True:
            state = utils.StateInterface.read()
            # idle until next measurement period
            seconds_to_wait_for_next_measurement = max(
                self.config.measurement.timing.seconds_per_measurement
                - (time.time() - self.last_measurement_time),
                0,
            )
            self.logger.debug(
                f"sleeping {round(seconds_to_wait_for_next_measurement, 3)} seconds"
            )
            time.sleep(seconds_to_wait_for_next_measurement)
            self.last_measurement_time = time.time()

            # Get latest auxilliary sensor data information
            self._update_air_inlet_parameters()

            # perform a CO2 measurement
            current_sensor_data = (
                self.hardware_interface.co2_sensor.get_current_concentration(
                    pressure=self.air_inlet_bme280_data.pressure,
                    humidity=self.air_inlet_sht45_data.humidity,
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
            ) >= self.config.measurement.timing.seconds_per_measurement_interval:
                break

        self.logger.info(f"finished measurement interval")
