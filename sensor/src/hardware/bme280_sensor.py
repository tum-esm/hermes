from typing import Literal, Optional
import smbus2
import bme280
from src import utils, custom_types


class BME280SensorInterface:
    @staticmethod
    class DeviceFailure(Exception):
        """raised when the sensor is not available"""

    def __init__(
        self,
        config: custom_types.Config,
        variant: Literal["mainboard", "air-inlet"],
        testing: bool = False,
    ) -> None:
        self.logger = utils.Logger(
            "mainboard-bme280" if (variant == "mainboard") else "air-inlet-bme280",
            print_to_console=testing,
            write_to_file=(not testing),
        )
        self.config = config
        self.variant = variant
        self.logger.info("Starting initialization")

        # set up connection to BME280 sensor
        self.bus = smbus2.SMBus(1)
        self.address = 0x77 if (variant == "mainboard") else 0x76
        self.compensation_params: Optional[bme280.params] = None
        self.logger.info("Finished initialization")

    def get_data(self) -> custom_types.BME280SensorData:
        """log mainboard and cpu temperature and enclosure humidity and pressure"""

        output = custom_types.BME280SensorData(
            temperature=None,
            humidity=None,
            pressure=None,
        )

        # returns None if no air-inlet sensor is connected
        if (self.variant == "air-inlet") and (
            self.config.active_components.ignore_missing_air_inlet_sensor
        ):
            return output

        # reads compensation values
        if self.compensation_params is None:
            self.read_compensation_param()

        # read bme280 data (retries 2 additional times)
        for _ in range(3):
            bme280_data: Optional[bme280.compensated_readings] = None
            try:
                bme280_data = bme280.sample(
                    self.bus,
                    self.address,
                    self.compensation_params,
                )
                output.temperature = round(bme280_data.temperature, 2)
                output.humidity = round(bme280_data.humidity, 2)
                output.pressure = round(bme280_data.pressure, 2)
                return output

            except Exception as e:
                self.logger.exception(
                    e,
                    label="exception during BME280 measurement request.",
                    config=self.config,
                )
                self.logger.warning(
                    "reinitialising sensor communication.",
                    config=self.config,
                )
                self._reset_sensor()

        # returns None if mainboard sensor could be read
        if self.variant == "mainboard":
            return output

        # raises device error if air-inlet sensor could be read
        raise BME280SensorInterface.DeviceFailure("could not fetch data")

    def check_errors(self) -> None:
        """Tries to fetch data, possibly raises `DeviceFailure`"""

        data = self.get_data()
        if data.temperature is None:
            raise BME280SensorInterface.DeviceFailure("could not fetch data")

    def read_compensation_param(self) -> None:
        try:
            self.compensation_params = bme280.load_calibration_params(
                self.bus, self.address
            )
        except Exception as e:
            self.logger.exception(
                e,
                label="could not fetch compensation params",
                config=self.config,
            )
            self.compensation_params = None

    def _reset_sensor(self) -> None:
        self.compensation_params = None
        self.teardown()
        self.bus = smbus2.SMBus(1)
        self.address = 0x77 if (self.variant == "mainboard") else 0x76
        self.read_compensation_param()
        self.logger.info("Starting initialization")

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.bus.close()
