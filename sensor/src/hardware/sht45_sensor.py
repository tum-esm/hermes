import busio
import board
import adafruit_sht4x
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
        self.config = config
        self.logger.info("Starting initialization")

        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sht = adafruit_sht4x.SHT4x(self.i2c)
        self.logger.debug(
            f"Found SHT4x with serial number {hex(self.sht.serial_number)}"
        )
        self.sht.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION

        self.logger.info("Finished initialization")

    def get_data(self) -> custom_types.SHT45SensorData:
        try:
            temperature, relative_humidity = self.sht.measurements
            return custom_types.SHT45SensorData(
                temperature=round(temperature, 2),
                humidity=round(relative_humidity, 2),
            )

        except Exception:
            self.logger.warning("could not sample data", config=self.config)
            if self.config.active_components.ignore_missing_air_inlet_sensor:
                return custom_types.SHT45SensorData(
                    temperature=None,
                    humidity=None,
                )
            raise SHT45SensorInterface.DeviceFailure("could not sample data")

    def check_errors(self) -> None:
        """Tries to fetch data, possibly raises `DeviceFailure`"""

        data = self.get_data()
        if data.temperature is None:
            raise SHT45SensorInterface.DeviceFailure("could not sample data")
