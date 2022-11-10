# Copyright (c) 2015 Martin Steppuhn, www.emsystech.de. Alle Rechte vorbehalten.
# https://github.com/Tronde/Raspi-SHT21

import time
from src import utils, types
from .i2c import I2CInterface

# TODO rename to inflow-air-sensor
class InputAirSensorInterface:
    def __init__(self, config: types.Config) -> None:
        self.i2c_interface = I2CInterface(0x40, 1)
        self.logger = utils.Logger(config, origin="input-air-sensor")

    def run(self, logger: bool = True) -> None:
        """Complete cycle including open, measurement und close, return tuple of temperature and humidity"""
        self.i2c_interface.write(
            [0xFE]
        )  # execute Softreset Command  (default T=14Bit RH=12)
        time.sleep(0.05)

        t = self._read_temperature()
        rh = self._read_humidity()
        self.i2c_interface.close()

        message = f"temperatur = {t}°C, humidity = {rh}%"
        if logger:
            self.logger.info(message)
        else:
            print(message)

    def _read_temperature(self) -> float | None:
        """Temperature measurement (no hold master), blocking for ~ 88ms !!!"""
        self.i2c_interface.write([0xF3])
        time.sleep(0.086)  # wait, typ=66ms, max=85ms @ 14Bit resolution
        data = self.i2c_interface.read(3)
        if self._check_crc(data, 2):
            t: float = ((data[0] << 8) + data[1]) & 0xFFFC  # set status bits to zero
            t = -46.82 + ((t * 175.72) / 65536)  # T = 46.82 + (175.72 * ST/2^16 )
            return round(t, 1)
        else:
            return None

    def _read_humidity(self) -> float | None:
        """RH measurement (no hold master), blocking for ~ 32ms !!!"""
        self.i2c_interface.write([0xF5])  # Trigger RH measurement (no hold master)
        time.sleep(0.03)  # wait, typ=22ms, max=29ms @ 12Bit resolution
        data = self.i2c_interface.read(3)
        if self._check_crc(data, 2):
            rh: float = ((data[0] << 8) + data[1]) & 0xFFFC  # zero the status bits
            rh = -6 + ((125 * rh) / 65536)
            if rh > 100:
                rh = 100
            return round(rh, 1)
        else:
            return None

    def _check_crc(self, data: bytes, length: int) -> bool:
        """Calculates checksum for n bytes of data and compares it with expected"""
        crc = 0
        for i in range(length):
            crc ^= ord(chr(data[i]))
            for bit in range(8, 0, -1):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x131  # CRC POLYNOMIAL
                else:
                    crc = crc << 1
        return crc == data[length]
