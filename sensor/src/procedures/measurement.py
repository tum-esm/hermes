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
        self.last_measurement_time: float = 0

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
        
        self.hardware_interface.co2_sensor.set_calibration_values(
            humidity=humidity,
            pressure=mainboard_data.enclosure_pressure,
        )

        # TODO: fetch chamber temperature from CO2 sensor

        utils.SendingMQTTClient.enqueue_message(
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
        # set up pump to run continuously
        self.hardware_interface.pump.set_desired_pump_speed(
            unit="litres_per_minute",
            value=self.config.measurement.pumped_litres_per_minute,
        )
        time.sleep(0.5)

        start_time = time.time()

        # possibly switches valve every two minutes
        self._update_input_valve()
        self._update_input_air_calibration()
        # TODO: send temperature data via mqtt

        # do regular measurements for about 2 minutes
        while True:
            now = time.time()
            if (
                now - start_time
                > self.config.measurement.timing.seconds_per_measurement_interval
            ):
                break

            time_since_last_measurement = now - self.last_measurement_time
            if (
                time_since_last_measurement
                < self.config.measurement.timing.seconds_per_measurement
            ):
                time.sleep(
                    self.config.measurement.timing.seconds_per_measurement
                    - time_since_last_measurement
                )
            self.last_measurement_time = now

            current_sensor_data = (
                self.hardware_interface.co2_sensor.get_current_concentration()
            )
            self.logger.info(f"new measurement: {current_sensor_data}")
            utils.SendingMQTTClient.enqueue_message(
                self.config,
                message_body=custom_types.MQTTDataMessageBody(
                    timestamp=round(time.time(), 2),
                    value=custom_types.MQTTCO2Data(
                        variant="co2", data=current_sensor_data
                    ),
                    revision=self.config.revision,
                ),
            )
