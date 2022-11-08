# Copyright (c) 2018 Matt Hawkins
# https://www.raspberrypi-spy.co.uk/

import smbus2
import bme280
import os
from src import utils, types

I2C_ADDR_INTERN = 0x77
I2C_ADDR_EXTERN = 0x76


class MainboardSensorInterface:
    def __init__(self, config: types.Config) -> None:
        self.i2c_device = smbus2.SMBus(1)
        self.logger = utils.Logger(config)

    def get_cpu_temperature(self):
        s = os.popen("vcgencmd measure_temp").readline()
        return float(s.replace("temp=", "").replace("'C\n", ""))

    def log_system_data(self, logger: bool = True) -> None:
        """Get the temperature, humidity and pressure of ACCOS and logs the data
        return: main_temp is the temperature of the Mainboard
                cpu_temp is the temperature of the RPI CPU
                pressure_system is the atmospheric pressure in the ACCOS
                humidity_system is the atmospheric pressure in the ACCOS
        """

        bus = smbus2.SMBus(1)
        calibration_params = bme280.load_calibration_params(bus, I2C_ADDR_EXTERN)
        data = bme280.sample(bus, I2C_ADDR_EXTERN, calibration_params)

        cpu_temperature = self.get_cpu_temperature()
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
