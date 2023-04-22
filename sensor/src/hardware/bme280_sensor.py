from typing import Literal, Optional
import smbus2
import bme280
import os
from src import utils, custom_types


class BME280SensorInterface:
    def __init__(
        self,
        config: custom_types.Config,
        address: Literal[0x76, 0x77] = 0x77,
    ) -> None:
        self.logger, self.config = utils.Logger("mainboard-sensor"), config
        self.logger.info("Starting initialization")

        # set up connection to BME280 sensor
        self.i2c_device = smbus2.SMBus(1)
        self.bus = smbus2.SMBus(1)
        self.address = address
        self.compensation_params: Optional[bme280.params] = None
        self.init_sensor()

        self.logger.info("Finished initialization")

    def init_sensor(self) -> None:
        try:
            self.compensation_params = bme280.load_calibration_params(
                self.bus, self.address
            )
        except OSError:
            self.logger.warning(
                "could not fetch compensation params", config=self.config
            )

    def get_data(self) -> custom_types.BME280SensorData:
        """log mainboard and cpu temperature and enclosure humidity and pressure"""

        if self.compensation_params is None:
            self.init_sensor()

        bme280_data: Optional[bme280.compensated_readings] = None
        output = custom_types.BME280SensorData(
            mainboard_temperature=None,
            enclosure_humidity=None,
            enclosure_pressure=None,
        )
        try:
            assert self.compensation_params is not None
            bme280_data = bme280.sample(
                self.bus,
                self.address,
                self.compensation_params,
            )
            custom_types.BME280SensorData(
                mainboard_temperature=round(bme280_data.temperature, 1),
                enclosure_humidity=round(bme280_data.humidity, 1),
                enclosure_pressure=round(bme280_data.pressure, 1),
            )
        except (AssertionError, OSError):
            self.logger.warning("could not sample data", config=self.config)

        return output

    def check_errors(self) -> None:
        """logs warnings when mainboard or CPU temperature are above 70°C"""
        system_data = self.get_system_data()

        if (system_data.mainboard_temperature is not None) and (
            system_data.mainboard_temperature > 70
        ):
            self.logger.warning(
                f"mainboard temperature is very high ({system_data.mainboard_temperature}°C)",
                config=self.config,
            )
        if (system_data.cpu_temperature is not None) and (
            system_data.cpu_temperature > 70
        ):
            self.logger.warning(
                f"cpu temperature is very high ({system_data.cpu_temperature}°C)",
                config=self.config,
            )

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.bus.close()
