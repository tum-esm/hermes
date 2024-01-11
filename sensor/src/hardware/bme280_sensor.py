import smbus2
import bme280
import time
from typing import Literal, Optional
from src import utils, custom_types


class BME280SensorInterface:
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
        self.logger.info("starting initialization")
        self.compensation_params: Optional[bme280.params] = None

        # set up connection to BME280 sensor
        self.sensor_connected = False
        for _ in range(2):
            try:
                self.bus = smbus2.SMBus(1)
                self.address = 0x77 if (variant == "mainboard") else 0x76

                # test if the sensor data can be read
                bme280.sample(
                    self.bus,
                    self.address,
                )

                # sensor didn't raise any issue during connection
                self.sensor_connected = True
                break
            except Exception as e:
                self.logger.exception(
                    e,
                    label=f"Could not initialize BME280 sensor (variant: {self.variant})",
                    config=self.config,
                )

            time.sleep(1)

        if not self.sensor_connected:
            self.logger.warning(
                f"Could not connect to BME280 sensor (variant: {self.variant}).",
                config=self.config,
            )

        self.logger.info("Finished initialization")

    def get_data(self, retries: int = 1) -> custom_types.BME280SensorData:
        """Reads temperature,humidity and pressure on mainboard and air inlet"""

        # initialize output
        output = custom_types.BME280SensorData(
            temperature=None,
            humidity=None,
            pressure=None,
        )

        # returns None if no air-inlet sensor is connected
        if not self.sensor_connected:
            self.logger.warning(
                f"Did not fetch BME280 sensor (variant: {self.variant}) data. Device is not connected.",
            )
            return output

        # sets compensation values once
        if self.compensation_params is None:
            self.read_compensation_param()

        # read bme280 data
        for _ in range(retries + 1):
            try:
                bme280_data = bme280.sample(
                    self.bus,
                    self.address,
                )
                output.temperature = round(bme280_data.temperature, 2)
                output.humidity = round(bme280_data.humidity, 2)
                output.pressure = round(bme280_data.pressure, 2)
                return output

            except Exception as e:
                self.logger.warning(
                    "Problem during sensor readout. Reinitialising sensor communication.",
                    config=self.config,
                )
                self._reset_sensor()

        # returns None if sensor could not be read
        self.logger.warning(
            "Could not read BME280 measurement values. Device is not connected.",
            config=self.config,
        )
        return output

    def read_compensation_param(self) -> None:
        try:
            self.compensation_params = bme280.load_calibration_params(
                self.bus, self.address
            )
        except Exception as e:
            self.logger.warning(
                "Could not fetch compensation params.",
            )
            self.compensation_params = None

    def _reset_sensor(self) -> None:
        try:
            self.compensation_params = None
            self.bus.close()
            time.sleep(1)
            self.bus = smbus2.SMBus(1)
            self.address = 0x77 if (self.variant == "mainboard") else 0x76

            # test if the sensor data can be read
            bme280.sample(
                self.bus,
                self.address,
            )

            self.read_compensation_param()
            self.logger.info(
                f"Reset sensor was successful.",
            )
            self.sensor_connected = True
            time.sleep(1)
        except Exception:
            self.logger.warning(
                f"Reset of the BME280 sensor (variant: {self.variant}) failed.",
            )
            self.sensor_connected = False

    def teardown(self) -> None:
        """Ends all hardware/system connections"""
        self.bus.close()
