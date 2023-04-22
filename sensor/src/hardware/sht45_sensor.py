import busio
import board
import adafruit_sht4x
from src import utils, custom_types


class SHT45SensorInterface:
    def __init__(self, config: custom_types.Config) -> None:
        self.logger, self.config = utils.Logger("sht45-sensor"), config
        self.logger.info("Starting initialization")

        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sht = adafruit_sht4x.SHT4x(self.i2c)
        self.logger.debug(
            f"Found SHT4x with serial number {hex(self.sht.serial_number)}"
        )

        self.sht.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION

        self.logger.info("Finished initialization")

    def get_data(self) -> custom_types.SHT45SensorData:
        """log mainboard and cpu temperature and enclosure humidity and pressure"""

        output = custom_types.SHT45SensorData(
            temperature=None,
            humidity=None,
        )
        try:
            temperature, relative_humidity = self.sht.measurements
            output.temperature = round(temperature, 2)
            output.humidity = round(relative_humidity, 2)

        except (AssertionError, OSError):
            self.logger.warning("could not sample data", config=self.config)

        return output
