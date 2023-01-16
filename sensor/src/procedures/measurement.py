# TODO: https://github.com/tum-esm/insert-name-here/issues/34

import time
from typing import Literal, Optional
from src import custom_types, utils, hardware_interfaces


class MeasurementProcedure:
    """
    runs every mainloop call when no configuration or calibration ran

    1. Check whether the wind and co2 sensor report any issues
    2. Check wind sensor direction and possibly change inlet
    3. Apply calibration using SHT 21 values
    4. Do 2 minutes of measurements
    """

    def __init__(self, config: custom_types.Config) -> None:
        self.logger = utils.Logger(origin="measurements")
        self.config = config

        # valve switching
        self.wind_sensor_interface = hardware_interfaces.WindSensorInterface(config)
        self.valve_interfaces = hardware_interfaces.ValveInterface(config)
        self.active_air_inlet: Optional[custom_types.MeasurementAirInletConfig] = None

        # pump (runs continuously)
        self.pump_interface = hardware_interfaces.PumpInterface(config)
        self.pump_interface.set_desired_pump_rps(
            self.config.measurement.pumped_litres_per_minute
            / (60 * self.config.hardware.pumped_litres_per_round)
        )
        time.sleep(1)

        # measurements
        self.air_inlet_sensor = hardware_interfaces.AirInletSensorInterface()
        self.co2_sensor_interface = hardware_interfaces.CO2SensorInterface(config)
        self.last_measurement_time: float = 0

    def _switch_to_air_inlet(
        self, new_air_inlet: custom_types.MeasurementAirInletConfig
    ) -> None:
        """
        1. switches to a different valve
        2. pumps 50 meters worth of air (or some other pipe length at the new valve)
        """

        self.valve_interfaces.set_active_input(new_air_inlet.valve_number)

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

    def _get_current_wind_data(self) -> custom_types.WindSensorData:
        """
        * fetches the latest wind sensor data
        * raises TimeoutError after 15 seconds without a response
        """
        start_time = time.time()

        while True:
            wind_data = self.wind_sensor_interface.get_current_wind_measurement()
            if wind_data is not None:
                return wind_data
            self.logger.debug("no current wind data, waiting 2 seconds")
            time.sleep(2)
            if time.time() - start_time > 15:
                raise TimeoutError(
                    "wind sensor did not send any wind data for 15 seconds"
                )

    def _update_input_valve(self) -> None:
        """
        1. fetches the current wind data from the wind sensor
        2. calculates which air inlet direction is the closest one
        3. possibly performs the switch between air inlets
        """

        # fetch wind data
        wind_data = self._get_current_wind_data()

        # determine new valve
        new_air_inlet = min(
            self.config.measurement.air_inlets,
            key=lambda x: utils.math.distance_between_angles(
                x.direction, wind_data.direction_avg
            ),
        )

        # perform switch
        if self.active_air_inlet is None:
            self.logger.info(f"enabeling air inlet {new_air_inlet.dict()}")
            self._switch_to_air_inlet(new_air_inlet)
        else:
            if wind_data.speed_avg < 0.2:
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
        _, humidity = self.air_inlet_sensor.get_current_values()
        self.co2_sensor_interface.set_calibration_values(humidity=humidity)
        if humidity is None:
            self.logger.warning(
                "could not read humidity value from SHT21", config=self.config
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

        start_time = time.time()

        # check whether sensors or pump report any errors
        self.co2_sensor_interface.check_errors()
        self.wind_sensor_interface.check_errors()
        self.pump_interface.check_errors()

        # possibly switches valve every two minutes
        self._update_input_valve()
        self._update_input_air_calibration()

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

            current_sensor_data = self.co2_sensor_interface.get_current_concentration()
            self.logger.info(f"new measurement: {current_sensor_data}")
            utils.SendingMQTTClient.enqueue_message(
                message_body=custom_types.MQTTMeasurementMessageBody(
                    timestamp=time.time(),
                    value=current_sensor_data,
                    revision=self.config.revision,
                ),
            )

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.wind_sensor_interface.teardown()
        self.valve_interfaces.teardown()
        self.pump_interface.teardown()
        self.co2_sensor_interface.teardown()
