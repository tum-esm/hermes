import time
from typing import Optional
from src import custom_types, utils, hardware


class MeasurementProcedure:
    """
    runs every mainloop call when no configuration or calibration ran

    1. Check whether the wind and co2 sensor report any issues
    2. Check wind sensor direction and possibly change inlet
    3. Apply calibration using SHT 21 values
    4. Do 2 minutes of measurements
    """

    def __init__(
        self,
        config: custom_types.Config,
        hardware_interface: hardware.HardwareInterface,
    ) -> None:
        self.logger, self.config = utils.Logger(origin="measurement-procedure"), config
        self.hardware_interface = hardware_interface

        # state variables
        self.active_air_inlet: Optional[custom_types.MeasurementAirInletConfig] = None
        self.last_iteration_start_time: float = 0
        self.active_mqtt_queue = utils.ActiveMQTTQueue()

    def _switch_to_air_inlet(
        self, new_air_inlet: custom_types.MeasurementAirInletConfig
    ) -> None:
        """
        1. switches to a different valve
        2. pumps air according to tube length
        """
        self.hardware_interface.valves.set_active_input(new_air_inlet.valve_number)

        # pump air out of the new tube
        tube_volume_in_litres = (
            3.141592
            * pow(self.config.hardware.inner_tube_diameter_millimiters * 0.5 * 0.01, 2)
            * new_air_inlet.tube_length
            * 10
        )
        required_pumping_time = tube_volume_in_litres / (
            self.config.measurement.pumped_litres_per_minute / 60
        )
        self.logger.debug(f"pumping {required_pumping_time} second(s)")
        time.sleep(required_pumping_time)

        self.active_air_inlet = new_air_inlet

    def _get_current_wind_data(self) -> Optional[custom_types.WindSensorData]:
        """fetches the latest wind sensor data and returns None if the
        wind sensor doesn't respond with any data"""
        wind_data = self.hardware_interface.wind_sensor.get_current_wind_measurement()
        if wind_data is None:
            self.logger.warning("no current wind data, waiting 2 seconds")
        return wind_data

    def _update_input_valve(self) -> None:
        """
        1. fetches the current wind data from the wind sensor
        2. calculates which air inlet direction is the closest one
        3. possibly performs the switch between air inlets
        """

        # fetch wind data
        wind_data = self._get_current_wind_data()

        # determine new valve
        if wind_data is not None:
            avg_dir = wind_data.direction_avg
            new_air_inlet = min(
                self.config.measurement.air_inlets,
                key=lambda x: utils.distance_between_angles(x.direction, avg_dir),
            )
            self.active_mqtt_queue.enqueue_message(
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

        else:
            new_air_inlet = list(
                filter(
                    lambda x: x.valve_number == 1,
                    self.config.measurement.air_inlets,
                )
            )[0]

        # perform switch
        if self.active_air_inlet is None:
            self.logger.info(f"enabeling air inlet {new_air_inlet.dict()}")
            self._switch_to_air_inlet(new_air_inlet)
        else:
            if (wind_data is not None) and (wind_data.speed_avg < 0.2):
                self.logger.debug(f"wind speed very low ({wind_data.speed_avg} m/s)")
                self.logger.info(f"staying at air inlet {self.active_air_inlet.dict()}")
            else:
                if self.active_air_inlet.valve_number != new_air_inlet.valve_number:
                    self.logger.info(f"switching to air inlet {new_air_inlet.dict()}")
                    self._switch_to_air_inlet(new_air_inlet)
                else:
                    self.logger.info(f"staying at air inlet {new_air_inlet.dict()}")

    def _update_input_air_calibration(self) -> None:
        """
        1. fetches the latest temperature and pressure data at air inlet
        2. sends these values to the CO2 sensor
        """
        (
            temperature,
            humidity,
        ) = self.hardware_interface.air_inlet_sensor.get_current_values()
        mainboard_data = self.hardware_interface.mainboard_sensor.get_system_data()

        self.hardware_interface.co2_sensor.set_compensation_values(
            humidity=humidity,
            pressure=mainboard_data.enclosure_pressure,
        )

        # TODO: fetch chamber temperature from CO2 sensor

        self.active_mqtt_queue.enqueue_message(
            self.config,
            custom_types.MQTTDataMessageBody(
                revision=self.config.revision,
                timestamp=round(time.time(), 2),
                value=custom_types.MQTTAirData(
                    variant="air",
                    data=custom_types.AirSensorData(
                        inlet_temperature=temperature,
                        inlet_humidity=humidity,
                        chamber_temperature=None,
                    ),
                ),
            ),
        )

    def run(self) -> None:
        """
        1. checks wind and co2 sensor for errors
        2. switches between input valves
        3. starts pumping
        4. calibrates co2 sensor with input air
        5. collects measurements for 2 minutes
        6. stops pumping

        the measurements will be sent to the MQTT client right
        during the collection (2 minutes)
        """
        self.logger.info(f"starting measurement interval")
        loop_start_time = time.time()

        # set up pump to run continuously
        self.hardware_interface.pump.set_desired_pump_speed(
            unit="litres_per_minute",
            value=self.config.measurement.pumped_litres_per_minute,
        )
        time.sleep(0.5)

        # set averaging time to time between datapoints
        self.hardware_interface.co2_sensor.set_filter_setting(
            average=self.config.measurement.timing.seconds_per_measurement
        )

        # possibly switches valve every two minutes
        self._update_input_valve()
        self._update_input_air_calibration()

        # do regular measurements for about 2 minutes
        while True:
            self.last_iteration_start_time = time.time()

            current_sensor_data = (
                self.hardware_interface.co2_sensor.get_current_concentration()
            )
            self.logger.debug(f"new measurement")
            self.active_mqtt_queue.enqueue_message(
                self.config,
                message_body=custom_types.MQTTDataMessageBody(
                    timestamp=round(time.time(), 2),
                    value=custom_types.MQTTCO2Data(
                        variant="co2", data=current_sensor_data
                    ),
                    revision=self.config.revision,
                ),
            )

            iteration_end_time = time.time()

            if (
                iteration_end_time - loop_start_time
            ) >= self.config.measurement.timing.seconds_per_measurement_interval:
                break

            elapsed_time = iteration_end_time - self.last_iteration_start_time
            remaining_sleep_seconds = (
                self.config.measurement.timing.seconds_per_measurement - elapsed_time
            )
            if remaining_sleep_seconds > 0:
                self.logger.debug(
                    f"sleeping {round(remaining_sleep_seconds, 3)} seconds"
                )
                time.sleep(remaining_sleep_seconds)

        self.logger.info(f"finished measurement interval")
