import fcntl
from typing import Literal
import serial
import re
import time


class SerialCO2SensorInterface:
    def __init__(self, port: str) -> None:
        self.serial_interface = serial.Serial(
            port=port,
            baudrate=19200,
            bytesize=8,
            parity="N",
            stopbits=1,
        )

    def send_command(self, message: str) -> None:
        """send a command to the sensor. Puts a "\x1B" string before the
        command, which will make the sensor wait until previous commands
        have been processed"""
        self.serial_interface.write((f"{message}\r\n").encode("utf-8"))
        self.serial_interface.flush()

    def flush_receiver_stream(self) -> None:
        """wait 0.2 seconds and then empty the current input queue"""
        time.sleep(0.2)  # wait for outstanding answers from previous commands
        self.serial_interface.read_all()

    def wait_for_answer(self, expected_regex: str = "[^>]*", timeout: float = 8) -> str:
        expected_pattern = re.compile(
            r"^(\r\n|\s)*" + expected_regex + r"(\r\n|\s)*>(\r\n|\s)*$"
        )
        start_time = time.time()
        answer = ""

        while True:
            received_bytes = self.serial_interface.read_all()
            if received_bytes is not None:
                answer += received_bytes.decode(encoding="cp1252")
                if expected_pattern.match(answer) is not None:
                    return answer

            if (time.time() - start_time) > timeout:
                raise TimeoutError(
                    "sensor did not answer as expected: expected_regex "
                    + f"= {repr(expected_regex)}, answer = {repr(answer)}"
                )
            else:
                time.sleep(0.05)


class SerialOneDirectionalInterface:
    def __init__(
        self,
        port: str,
        baudrate: Literal[19200, 9600],
        encoding: Literal["cp1252", "utf-8"] = "utf-8",
        line_endling: str = "\n",
    ) -> None:
        self.serial_interface = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
        )
        self.current_input_stream = ""
        self.encoding = encoding
        self.line_ending = line_endling

    def get_messages(self) -> list[str]:
        new_input_bytes = self.serial_interface.read_all()
        if new_input_bytes is None:
            return []

        self.current_input_stream += new_input_bytes.decode(self.encoding)
        separate_messages = self.current_input_stream.split(self.line_ending)
        self.current_input_stream = separate_messages[-1]
        return separate_messages[:-1]

    def close(self) -> None:
        """close connection"""
        self.serial_interface.close()


class SerialI2CInterface:
    def __init__(self, address: int = 0, device: int = 1) -> None:
        """Open I2C-Port

        addr: I2C device address
        dev:  I2C port (Raspberry Pi) B,B+,Pi 2 = 1 the first Pi = 0
              For I2C emulation with GPIO, dev must be None
        """
        self.i2c_device = open(("/dev/i2c-%s" % device), "rb+", 0)
        fcntl.ioctl(self.i2c_device, 0x0706, address)  # I2C Address

    def close(self) -> None:
        """close connection"""
        self.i2c_device.close()

    def write(self, data: list[int]) -> None:
        """write data to device"""
        self.i2c_device.write(bytes(data))

    def read(self, n: int) -> bytes:
        """read n bytes from I2C device"""
        return self.i2c_device.read(n)
