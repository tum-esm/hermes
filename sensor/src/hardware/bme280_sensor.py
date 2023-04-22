from typing import Literal, Optional
import smbus2
import bme280
from src import utils, custom_types


class BME280SensorInterface:
    def __init__(
        self,
        config: custom_types.Config,
        variant: Literal["mainboard", "air inlet"],
    ) -> None:
        self.logger, self.config = utils.Logger("mainboard-sensor"), config
        self.logger.info("Starting initialization")

        # set up connection to BME280 sensor
        self.i2c_device = smbus2.SMBus(1)
        self.bus = smbus2.SMBus(1)
        self.address = 0x77 if variant == "mainboard" else 0x76
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
            temperature=None,
            humidity=None,
            pressure=None,
        )
        try:
            assert self.compensation_params is not None
            bme280_data = bme280.sample(
                self.bus,
                self.address,
                self.compensation_params,
            )
            output.temperature = round(bme280_data.temperature, 1)
            output.humidity = round(bme280_data.humidity, 1)
            output.pressure = round(bme280_data.pressure, 1)

        except (AssertionError, OSError):
            self.logger.warning("could not sample data", config=self.config)

        return output

    # TODO: move these checks into syste checks module
    def check_errors(self) -> None:
        """logs warnings when mainboard or CPU temperature are above 70°C"""
        data = self.get_data()

        if (data.temperature is not None) and (data.temperature > 70):
            self.logger.warning(
                f"mainboard temperature is very high ({data.temperature}°C)",
                config=self.config,
            )

        # if (system_data.cpu_temperature is not None) and (
        #     system_data.cpu_temperature > 70
        # ):
        #     self.logger.warning(
        #         f"cpu temperature is very high ({system_data.cpu_temperature}°C)",
        #         config=self.config,
        #     )

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.bus.close()