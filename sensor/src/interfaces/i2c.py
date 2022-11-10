# Copyright (c) 2015 Martin Steppuhn, www.emsystech.de. Alle Rechte vorbehalten.
# https://github.com/Tronde/Raspi-SHT21

import fcntl


class I2CInterface:
    def __init__(self, addr: int = 0, dev: int = 1) -> None:
        """Open I2C-Port

        addr: I2C device address
        dev:  I2C port (Raspberry Pi) B,B+,Pi 2 = 1 the first Pi = 0
              For I2C emulation with GPIO, dev must be None
        """
        self.i2c_device = open(("/dev/i2c-%s" % dev), "rb+", 0)
        fcntl.ioctl(self.i2c_device, 0x0706, addr)  # I2C Address

    def close(self) -> None:
        """close connection"""
        self.i2c_device.close()

    def write(self, data: list[int]) -> None:
        """write data to device"""
        self.i2c_device.write(bytes(data))

    def read(self, n: int) -> bytes:
        """read n bytes from I2C device"""
        return self.i2c_device.read(n)
