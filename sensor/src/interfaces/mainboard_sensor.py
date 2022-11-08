# Copyright (c) 2018 Matt Hawkins
# https://www.raspberrypi-spy.co.uk/

import smbus2
import bme280
import os

I2C_ADDR_INTERN = 0x77
I2C_ADDR_EXTERN = 0x76


class MainboardSensorInterface:
    def __init__(self) -> None:
        self.i2c_device = smbus2.SMBus(1)

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

        cpu_temp = self.get_cpu_temperature()
        """data = (
            f"Mainboard_temp {round(main_temp,1)}°C, "
            + f"CPU_temp {round(cpu_temp,1)}°C, "
            + f"Humidity {round(humidity_system,1)}%, "
            + f"Pressure {round(pressure_system,2)}hPa"
        )"""

        message = f"{data}, {cpu_temp}"
        if logger:
            self.logger.info(message)
        else:
            print(message)

        # TODO: if main_temp > 40 or cpu_temp > 70: logger.system_data_logger.warning(data)
