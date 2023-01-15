from typing import Optional
import smbus2
import bme280
import os
from src import utils, custom_types


class MainboardSensorInterface:
    def __init__(self) -> None:
        self.i2c_device = smbus2.SMBus(1)
        self.bus = smbus2.SMBus(1)
        self.calibration_params = bme280.load_calibration_params(
            self.bus,
            utils.Constants.MainboardSensor.i2c_address,
        )

    def _get_cpu_temperature(self) -> Optional[float]:
        s = os.popen("vcgencmd measure_temp").readline()
        return float(s.replace("temp=", "").replace("'C\n", ""))

    def get_system_data(self) -> custom_types.MainboardSensorData:
        """log mainboard and cpu temperature and enclosure humidity and pressure"""

        bme280_data = bme280.sample(
            self.bus,
            utils.Constants.MainboardSensor.i2c_address,
            self.calibration_params,
        )
        return custom_types.MainboardSensorData(
            mainboard_temperature=round(bme280_data.temperature, 1),
            cpu_temperature=self._get_cpu_temperature(),
            enclosure_humidity=round(bme280_data.humidity, 1),
            enclosure_pressure=round(bme280_data.pressure, 1),
        )

    def check_errors(self) -> None:
        """logs warnings when mainboard or CPU temperature are above 70°C"""
        system_data = self.get_system_data()

        if system_data.mainboard_temperature > 70:
            self.logger.warning(
                f"mainboard temperature is very high ({system_data.mainboard_temperature}°C)",
                config=self.config,
            )
        if system_data.cpu_temperature is not None and system_data.cpu_temperature > 70:
            self.logger.warning(
                f"cpu temperature is very high ({system_data.cpu_temperature}°C)",
                config=self.config,
            )
