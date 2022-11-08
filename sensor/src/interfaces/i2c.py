# Copyright (c) 2015 Martin Steppuhn, www.emsystech.de. Alle Rechte vorbehalten.
# https://github.com/Tronde/Raspi-SHT21

import fcntl


class I2CInterface:
    """Wrapper class for I2C with raspberry Pi"""

    def __init__(self, addr: int = 0, dev: int = 1) -> None:
        """Open I2C-Port

        addr: I2C device address
        dev:  I2C port (Raspberry Pi) B,B+,Pi 2 = 1 the first Pi = 0
              For I2C emulation with GPIO, dev must be None
        """
        self.i2c_device = open(("/dev/i2c-%s" % dev), "rb+", 0)
        fcntl.ioctl(self.i2c_device, 0x0706, addr)  # I2C Address

    def close(self) -> None:
        self.i2c_device.close()

    def write(self, data: list[bytes | int]) -> None:
        """Write data to device"""
        self.dev_i2c.write(bytes(data))

    def read(self, size: int) -> bytes:
        """Read bytes from I2C device

        size: number of bytes to read
        """
        return self.i2c_device.read(size)
