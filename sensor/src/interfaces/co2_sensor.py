import re
import serial
import time
from src import utils, types
import gpiozero
import gpiozero.pins.pigpio

# returned when calling "errs"
error_regex = r"OK: No errors detected\."

# returned when powering up the sensor
startup_regex = r"GMP343 \- Version STD \d+\.\d+\r\nCopyright: Vaisala Oyj \d{4} - \d{4}"

# returned when calling "send"
concentration_regex = r"Raw\s*\d+\.\d ppm; Comp\.\s*\d+\.\d ppm; Filt\.\s*\d+\.\d ppm"

# returned when calling "corr"
# TODO

# returned when calling "average x"/"smooth x"/"median x"/"linear x"
filter_settings_regex = r"(AVERAGE \(s\)|SMOOTH|MEDIAN|LINEAR)\s*:\s(\d{1,3}|ON|OFF)"

# returned when calling "??"
sensor_info_regex = r"\s*\r\n".join(
    [
        r"GMP343 \/ \d+\.\d+",
        r"SNUM\s*: .*",
        r"CALIBRATION\s*: \d{4}\-\d{2}\-\d{2}",
        r"CAL\. INFO\s*: .*",
        r"SPAN \(ppm\)\s*: 1000",
        r"PRESSURE \(hPa\)\s*: \d+\.\d+\s*",
        r"HUMIDITY \(%RH\)\s*: \d+\.\d+\s*",
        r"OXYGEN \(%\)\s*: \d+\.\d+\s*",
        r"PC\s*: (ON|OFF)",
        r"RHC\s*: (ON|OFF)",
        r"TC\s*: (ON|OFF)",
        r"OC\s*: (ON|OFF)",
        r"ADDR\s*: \d*\s*",
        r"ECHO\s*: OFF",
        r"SERI\s*: 19200 8 NONE 1",
        r"SMODE\s*: .*",
        r"INTV\s*: \d+ .*",
    ]
)

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

    def wait_for_answer(self, expected_regex: str, timeout: float = 8) -> str:
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
    def __init__(self, config: types.Config, logger: utils.Logger | None = None) -> None:
        self.rs232_interface = RS232Interface()
        self.logger = logger if logger is not None else utils.Logger(config, origin="co2-sensor")
        self.pin_factory = utils.get_pin_factory()
        self.power_pin = gpiozero.OutputDevice(
            pin=utils.Constants.co2_sensor.power_pin_out, pin_factory=self.pin_factory
        )
        self._reset_sensor()

    def _reset_sensor(self) -> None:
        """will reset the sensors default settings. takes about 6 seconds"""

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
        self.set_filter_setting()

    def set_filter_setting(
        self,
        median: int = 0,
        average: int = 10,
        smooth: int = 0,
        linear: bool = True,
    ) -> None:
        """update the filter settings on the sensor"""

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

    def get_sensor_info(self) -> str:
        self.rs232_interface.flush_receiver_stream()
        self.rs232_interface.send_command("??")
        answer = self.rs232_interface.wait_for_answer(expected_regex=sensor_info_regex)
        return (
            answer.strip(" \r\n")
            .replace("  ", "")
            .replace(" : ", ": ")
            .replace(" \r\n", "; ")
            .replace("\r\n", "; ")
            .removesuffix("; >")
        )

    def log_sensor_correction_info(self) -> None:
        self.rs232_interface.flush_receiver_stream()
        self.rs232_interface.send_command("corr")
        # TODO: wait for sensor answer in an expected regex

    def log_sensor_errors(self) -> None:
        self.rs232_interface.flush_receiver_stream()
        self.rs232_interface.send_command("errs")
        # TODO: wait for sensor answer in an expected regex

    def teardown(self) -> None:
        """End all hardware connections"""
        self.pin_factory.close()
