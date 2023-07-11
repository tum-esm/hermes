import time
from typing import Optional
from src import custom_types, utils, hardware


class MeasurementProcedure:
    """runs every mainloop call after possible configuration/calibration

    1. Check whether the wind and co2 sensor report any issues
    3. Read inlet pressure and humidity
    4. Perform measurements"""

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
        self.chamber_temperature = (
            self.hardware_interface.co2_sensor.get_current_chamber_temperature()
        )

    def _send_latest_wind_data(self) -> None:
        # wind measurement
        wind_data = self.hardware_interface.wind_sensor.get_current_wind_measurement()

        # determine new valve
        if wind_data is not None:
            self.logger.info(f"sending latest wind data: {wind_data}")

            self.message_queue.enqueue_message(
                self.config,
                custom_types.MQTTDataMessageBody(
                    revision=self.config.revision,
                    timestamp=round(time.time(), 2),
                    value=custom_types.MQTTWindData(
                        variant="wind",
                        data=wind_data,
                    ),
                ),
            )

    def run(self) -> None:
        """
        1. checks wind and co2 sensor for errors
        2. switches between input valves
        4. sends air parameters to co2 sensor for compensation
        5. collects measurements for 2 minutes

        the measurements will be sent to the MQTT client right
        during the collection (2 minutes)
        """
        self.logger.info(f"starting 2 minute measurement interval")
        measurement_procedure_start_time = time.time()

        # Send wind data
        self._send_latest_wind_data()

        # do regular measurements for about 2 minutes
        while True:
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
                custom_types.MQTTDataMessageBody(
                    revision=self.config.revision,
                    timestamp=round(time.time(), 2),
                    value=custom_types.MQTTMeasurementData(
                        variant="measurement",
                        data=custom_types.MeasurementProcedureData(
                            raw=current_sensor_data.raw,
                            compensated=current_sensor_data.compensated,
                            filtered=current_sensor_data.filtered,
                            bme280_temperature=self.air_inlet_bme280_data.temperature,
                            bme280_humidity=self.air_inlet_bme280_data.humidity,
                            bme280_pressure=self.air_inlet_bme280_data.pressure,
                            sht45_temperature=self.air_inlet_sht45_data.temperature,
                            sht45_humidity=self.air_inlet_sht45_data.humidity,
                            chamber_temperature=self.chamber_temperature,
                        ),
                    ),
                ),
            )

            # stop loop after defined measurement interval
            if (
                self.last_measurement_time - measurement_procedure_start_time
            ) >= self.config.measurement.timing.seconds_per_measurement_interval:
                break

        self.logger.info(f"finished measurement interval")
