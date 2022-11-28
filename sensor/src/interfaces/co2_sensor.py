import re
import serial
import time
from src import utils, types
import gpiozero
import gpiozero.pins.pigpio

# returned when powering up the sensor
startup_regex = r"GMP343 \- Version STD \d+\.\d+\r\nCopyright: Vaisala Oyj \d{4} - \d{4}"

# returned when calling "send"
concentration_regex = r"Raw\s*\d+\.\d ppm; Comp\.\s*\d+\.\d ppm; Filt\.\s*\d+\.\d ppm"

# TODO: add pressure calibration
# TODO: add humidity calibration
# TODO: add oxygen calibration
# TODO: add temperature calibration


class RS232Interface:
    def __init__(self) -> None:
        self.serial_interface = serial.Serial(
            port="/dev/ttySC0",
            baudrate=19200,
            bytesize=8,
            parity="N",
            stopbits=1,
        )

    def send_command(self, message: str) -> None:
        """send a command to the sensor. Puts a "\x1B" string before the
        command, which will make the sensor wait until previous commands
        have been processed"""
        self.serial_interface.write((f"\x1B {message}\r\n").encode("utf-8"))
        self.serial_interface.flush()

    def flush_receiver_stream(self) -> None:
        """wait 0.2 seconds and then empty the current input queue"""
        time.sleep(0.2)  # wait for outstanding answers from previous commands
        self.serial_interface.read_all()

    def wait_for_answer(self, expected_regex: str = "[^>]*", timeout: float = 8) -> str:
        expected_pattern = re.compile(r"^(\r\n|\s)*" + expected_regex + r"(\r\n|\s)*>(\r\n|\s)*$")
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


class CO2SensorInterface:
    class DeviceFailure(Exception):
        """raised when the CO2 probe "errs" command responds with an error"""

    def __init__(self, config: types.Config, logger: utils.Logger | None = None) -> None:
        self.rs232_interface = RS232Interface()
        self.logger = logger if logger is not None else utils.Logger(config, origin="co2-sensor")
        self.pin_factory = utils.get_pin_factory()
        self.power_pin = gpiozero.OutputDevice(
            pin=utils.Constants.co2_sensor.power_pin_out, pin_factory=self.pin_factory
        )
        self._reset_sensor()

    def _reset_sensor(self) -> None:
        """reset the sensors default settings by turning it off and on and
        sending the initial settings again"""

        self.logger.info("(re)initializing default sensor settings")

        self.logger.debug("powering down sensor")
        self.power_pin.off()
        time.sleep(1)

        self.logger.debug("powering up sensor")
        self.rs232_interface.flush_receiver_stream()
        self.power_pin.on()
        self.rs232_interface.wait_for_answer(expected_regex=startup_regex)

        self.logger.debug("sending default settings")
        for default_setting in [
            "echo off",
            "range 1",
            'form "Raw " CO2RAWUC " ppm; Comp." CO2RAW " ppm; Filt. " CO2 " ppm"',
        ]:
            self.rs232_interface.send_command(default_setting)

        # set default filters
        # self.set_filter_setting()

    def set_filter_setting(
        self,
        median: int = 0,
        average: int = 10,
        smooth: int = 0,
        linear: bool = True,
    ) -> None:
        """update the filter settings on the CO2 probe"""

        # TODO: construct a few opinionated measurement setups

        assert average >= 0 and average <= 60, "invalid calibration setting, average not in [0, 60]"
        assert smooth >= 0 and smooth <= 255, "invalid calibration setting, smooth not in [0, 255]"
        assert median >= 0 and median <= 13, "invalid calibration setting, median not in [0, 13]"

        self.rs232_interface.send_command(f"average {average}")
        self.rs232_interface.send_command(f"smooth {smooth}")
        self.rs232_interface.send_command(f"median {median}")
        self.rs232_interface.send_command(f"linear {'on' if linear else 'off'}")
        time.sleep(0.5)

        self.logger.info(
            f"Updating filter settings (average = {average}, smooth"
            + f" = {smooth}, median = {median}, linear = {linear})"
        )

    def get_current_concentration(self) -> types.CO2SensorData:
        """get the current concentration value from the CO2 probe"""
        self.rs232_interface.flush_receiver_stream()
        self.rs232_interface.send_command("send")
        answer = self.rs232_interface.wait_for_answer(expected_regex=concentration_regex)
        for s in [" ", "Raw", "ppm", "Comp.", "Filt.", ">", "\r\n"]:
            answer = answer.replace(s, "")
        raw_value_string, comp_value_string, filt_value_string = answer.split(";")
        return types.CO2SensorData(
            raw=float(raw_value_string),
            compensated=float(comp_value_string),
            filtered=float(filt_value_string),
        )

    def _format_raw_answer(self, raw: str) -> str:
        """replace all useless characters in the CO2 probe's answer"""
        return (
            raw.strip(" \r\n")
            .replace("  ", "")
            .replace(" : ", ": ")
            .replace(" \r\n", "\r\n")
            .replace("\r\n\r\n", "\r\n")
            .replace("\r\n", "; ")
            .removesuffix("; >")
        )

    def get_device_info(self) -> str:
        """runs the "??" command to get a report about the sensor state"""
        self.rs232_interface.flush_receiver_stream()
        self.rs232_interface.send_command("??")
        return self._format_raw_answer(self.rs232_interface.wait_for_answer())

    def get_correction_info(self) -> str:
        """runs the "corr" command to retrieve information about the correction
        the CO2 probe currently uses"""
        self.rs232_interface.flush_receiver_stream()
        self.rs232_interface.send_command("corr")
        return self._format_raw_answer(self.rs232_interface.wait_for_answer())

    def check_sensor_errors(self) -> None:
        """checks whether the CO2 probe reports any errors. Possibly raises
        the CO2SensorInterface.DeviceFailure exception"""
        self.rs232_interface.flush_receiver_stream()
        self.rs232_interface.send_command("errs")
        answer = self._format_raw_answer(self.rs232_interface.wait_for_answer())

        if not ("OK: No errors detected" in answer):
            raise CO2SensorInterface.DeviceFailure(answer)

    def teardown(self) -> None:
        """End all hardware connections"""
        self.pin_factory.close()
