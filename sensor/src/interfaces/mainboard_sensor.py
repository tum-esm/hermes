import smbus2
import bme280
import os
from src import utils, types


class MainboardSensorInterface:
    def __init__(self, config: types.Config) -> None:
        self.i2c_device = smbus2.SMBus(1)
        self.logger = utils.Logger(config)

        self.bus = smbus2.SMBus(1)
        self.calibration_params = bme280.load_calibration_params(
            self.bus,
            utils.Constants.mainboard_sensor.i2c_address,
        )

    def _get_cpu_temperature(self) -> float:
        s = os.popen("vcgencmd measure_temp").readline()
        return float(s.replace("temp=", "").replace("'C\n", ""))

    def log_system_data(self, logger: bool = True) -> None:
        """log mainboard and cpu temperature and enclosure humidity and pressure"""

        data = bme280.sample(
            self.bus,
            utils.Constants.mainboard_sensor.i2c_address,
            self.calibration_params,
        )
        cpu_temperature = self._get_cpu_temperature()

        message_1 = (
            f"mainboard temp. = {round(data.temperature, 1)}°C, "
            + f"raspi cpu temp. = {round(cpu_temperature, 1)}°C"
        )
        message_2 = (
            f"enclosure humidity = {round(data.humidity, 1)} % rH, "
            + f"enclosure pressure = {round(data.pressure, 1)} hPa"
        )
        if logger:
            self.logger.info(message_1)
            self.logger.info(message_2)
        else:
            print(message_1)
            print(message_2)

        # TODO: if main_temp > 40 or cpu_temp > 70: logger.system_data_logger.warning(data)
