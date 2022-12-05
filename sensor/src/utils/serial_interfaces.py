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
