import busio
import adafruit_sht4x
import board
import time
from src import utils, custom_types


class SHT45SensorInterface:
    @staticmethod
    class DeviceFailure(Exception):
        """raised when the sensor is not available"""

    def __init__(
        self,
        config: custom_types.Config,
        testing: bool = False,
    ) -> None:
        self.logger = utils.Logger(
            origin="sht45-sensor",
            print_to_console=testing,
            write_to_file=(not testing),
        )
        self.broken_sensor = False
        self.config = config

        self.logger.info("Starting initialization")

        if not self.config.hardware.mock_air_inlet_sensors:
            # set up connection to SHT45 sensor
            try:
                self.i2c = busio.I2C(board.SCL, board.SDA)
                self.sht = adafruit_sht4x.SHT4x(self.i2c)
                self.logger.debug(
                    f"Found SHT4x with serial number {hex(self.sht.serial_number)}"
                )
                self.sht.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
            except Exception as e:
                self.logger.exception(
                    e,
                    label="could not initialize SHT45 sensor",
                    config=self.config,
                )
                self.broken_sensor = True

        self.logger.info("Finished initialization")

    def get_data(self) -> custom_types.SHT45SensorData:
        """reads temperature and humidity in the air inlet"""

        # initialize output
        output = custom_types.SHT45SensorData(
            temperature=None,
            humidity=None,
        )

        # returns None if no air-inlet sensor is connected
        if self.config.hardware.mock_air_inlet_sensors or self.broken_sensor:
            return output

        # read sht45 data (retries 2 additional times)
        for _ in range(3):
            try:
                temperature, relative_humidity = self.sht.measurements
                output.temperature = round(temperature, 2)
                output.humidity = round(relative_humidity, 2)
                return output

            except Exception as e:
                self.logger.exception(
                    e,
                    label="exception during BME280 measurement request",
                    config=self.config,
                )
                self.logger.warning(
                    "reinitialising sensor communication",
                    config=self.config,
                )
                self._reset_sensor()

        # returns None if sensor could not be read
        self.logger.warning(
            "could not read BME280 measurement values",
            config=self.config,
        )
        return output

    def check_errors(self) -> None:
        """Tries to fetch data, possibly raises `DeviceFailure`"""

        data = self.get_data()
        if data.temperature is None:
            raise SHT45SensorInterface.DeviceFailure("could not sample data")

    def _reset_sensor(self) -> None:
        self.sht.reset()
        time.sleep(1)
