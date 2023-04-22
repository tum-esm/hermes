import os
import sys
from typing import Optional
import smbus2
import bme280

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, hardware


config = utils.ConfigInterface.read()


for BME280_I2C_ADDRESS in [0x76, 0x77]:
    i2c_device = smbus2.SMBus(1)
    bus = smbus2.SMBus(1)
    compensation_params = bme280.load_calibration_params(bus, BME280_I2C_ADDRESS)
    bme280_data = bme280.sample(bus, BME280_I2C_ADDRESS, compensation_params)
    print(bme280_data)

# air_inlet = hardware.AirInletSensorInterface(config)
# print("humidity =", air_inlet.get_current_humidity())
# print("temperature =", air_inlet.get_current_temperature())

from smbus2 import SMBus

bus = SMBus(1)

for a in range(0x000, 0xFFF):
    try:
        bus.write_byte_data(a, 0, 0)
        print(f"{hex(a)} exists")
    except OSError:
        pass
bus.close()


sht45 = hardware.AirInletSensorInterface(config)
print(sht45.get_current_humidity())
print(sht45.get_current_temperature())

# import busio
# import adafruit_sht4x

# sht = adafruit_sht4x.SHT4x(busio.I2C())

# POSSIBLE SHT LIBRARIES:
#   adafruit-circuitpython-sht4x = "^1.0.15"
#   rpi-gpio = "^0.7.1"
#   sensirion-i2c-sht = "^0.3.0"
