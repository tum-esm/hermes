import queue
import re
import serial
import time
import threading
from src import utils, types
import gpiozero

# returned when calling "errs"
error_regex = r"OK: No errors detected\."

# returned when calling "corr"
# TODO

# returned when calling "average x"/"smooth x"/"median x"/"linear x"
filter_settings_regex = r"(AVERAGE \(s\)|SMOOTH|MEDIAN|LINEAR)\s*:\s(\d{1,3}|ON|OFF)"

# returned when calling "??"
sensor_info_regex = r"\n".join(
    [
        r"GMP343 / \d+\.\d+",
        r"SNUM           : .*",
        r"CALIBRATION    : \d{4}\-\d{4}\-\d{4}",
        r"CAL\. INFO      : .*",
        r"SPAN \(ppm\)     : 1000",
        r"PRESSURE \(hPa\) : \d+\.\d+",
        r"HUMIDITY \(%RH\) : \d+\.\d+",
        r"OXYGEN \(%\)     : \d+\.\d+",
        r"PC             : (ON|OFF)",
        r"RHC            : (ON|OFF)",
        r"TC             : (ON|OFF)",
        r"OC             : (ON|OFF)",
        r"ADDR           : .*",
        r"ECHO           : OFF",
        r"SERI           : 19200 8 NONE 1",
        r"SMODE          : .*",
        r"INTV           : .*",
    ]
)

# TODO: add pressure calibration
# TODO: add humidity calibration
# TODO: add oxygen calibration
# TODO: add temperature calibration

rs232_lock = threading.Lock()
rs232_receiving_stream: queue.Queue[str] = queue.Queue()


class NoAnswer(Exception):
    """raised when the communication partner doesn't answer as expected"""


class _RS232Interface:
    def __init__(self) -> None:
        self.serial_interface = serial.Serial("/dev/ttySC0", 19200)

    def write(
        self,
        message: str,
        sleep: float | None = None,
        send_esc: bool = False,
        save_eeprom: bool = False,
    ) -> None:
        with rs232_lock:
            self.serial_interface.write(
                (("\x1B " if send_esc else "") + message + "\r\n").encode("utf-8")
            )
            if save_eeprom:
                self.serial_interface.write("save\r\n".encode("utf-8"))
            self.serial_interface.flush()

        if sleep is not None:
            time.sleep(sleep)

    def flush_receiver_stream(self) -> None:
        while True:
            try:
                rs232_receiving_stream.get_nowait()
            except queue.Empty:
                break

    def get_answer(self, wait_time_before_read: float = 0.5, expected_regex: str = ".*") -> str:
        """look for a regex in the message stream that has been received since last calling this function"""
        time.sleep(wait_time_before_read)

        answer = ""
        while True:
            try:
                answer += rs232_receiving_stream.get_nowait()
            except queue.Empty:
                break

        if re.compile(f"^{expected_regex}$").match(answer) is None:
            raise NoAnswer(
                "sensor did not answer as expected: expected_regex "
                + f"= {expected_regex}, answer = {answer}"
            )
        return answer

    @staticmethod
    def data_receiving_loop(queue: queue.Queue[str]) -> None:
        """receiving all the data that is send over RS232 and put all completed
        lines into the rs232_receiving_queue"""
        rs232_interface = _RS232Interface()
        while True:
            waiting_byte_count = rs232_interface.serial_interface.in_waiting
            if waiting_byte_count > 0:
                received_bytes: bytes = rs232_interface.serial_interface.read(waiting_byte_count)
                received_string: str = received_bytes.decode(encoding="cp1252").replace(";", ",")
                queue.put(received_string)
            time.sleep(0.05)


class CO2SensorInterface:
    def __init__(self, config: types.Config, logger: utils.Logger = None) -> None:
        self.rs232_interface = _RS232Interface()
        self.logger = logger if logger is not None else utils.Logger(config, origin="co2-sensor")
        self.sensor_power_pin = gpiozero.OutputDevice(pin=utils.Constants.co2_sensor.pin_power_out)

        self._reset_sensor()

        self.logger.info("starting RS232 receiver thread")
        threading.Thread(
            target=_RS232Interface.data_receiving_loop, args=(rs232_receiving_stream,), daemon=True
        ).start()

    def _reset_sensor(self) -> None:
        """will reset the sensors default settings. takes about 6 seconds"""

        self.logger.info("reinitializing default sensor settings")

        self.logger.debug("powering down sensor")
        self.sensor_power_pin.off()
        time.sleep(1)

        self.logger.debug("powering up sensor")
        self.sensor_power_pin.on()
        time.sleep(3)

        for default_setting in [
            "echo off",
            "range 1000",
            'form "Raw " CO2RAWUC " ppm; Comp." CO2RAW " ppm; Filt. " CO2 " ppm" #r#n',
        ]:
            self.rs232_interface.write(default_setting, send_esc=True, save_eeprom=True, sleep=0.5)

        # set default filters
        self.set_filter_setting()

    def set_filter_setting(
        self,
        median: int = 0,
        average: int = 10,
        smooth: int = 0,
        linear: bool = True,
    ) -> None:
        """update the filter settings on the sensor. These will not
        be saved to the sensors eeprom"""

        # TODO: construct a few opinionated measurement setups

        assert average >= 0 and average <= 60, "invalid calibration setting, average not in [0, 60]"
        assert smooth >= 0 and smooth <= 255, "invalid calibration setting, smooth not in [0, 255]"
        assert median >= 0 and median <= 13, "invalid calibration setting, median not in [0, 13]"

        self.rs232_interface.write(f"average {average}", send_esc=True)
        self.rs232_interface.write(f"smooth {smooth}", send_esc=True)
        self.rs232_interface.write(f"median {median}", send_esc=True)
        self.rs232_interface.write(f"linear {'on' if linear else 'off'}", send_esc=True, sleep=0.5)
        self.logger.info(
            f"Updating filter settings (average = {average}, smooth"
            + f" = {smooth}, median = {median}, linear = {linear})"
        )

    def get_current_concentration(self) -> types.CO2SensorData:
        self.rs232_interface.flush_receiver_stream()
        self.rs232_interface.write("send")
        answer = self.rs232_interface.get_answer(
            expected_regex=r"Raw\s*\d+\.\d ppm; Comp\.\s*\d+\.\d ppm; Filt\.\s*\d+\.\d ppm"
        )
        print(answer)
        return types.CO2SensorData(raw=0, compensated=0, filtered=0)

    def log_sensor_info(self) -> None:
        self.rs232_interface.flush_receiver_stream()
        self.rs232_interface.write("??")
        # TODO: wait for sensor answer in an expected regex

    def log_sensor_correction_info(self) -> None:
        self.rs232_interface.flush_receiver_stream()
        self.rs232_interface.write("corr")
        # TODO: wait for sensor answer in an expected regex

    def log_sensor_errors(self) -> None:
        self.rs232_interface.flush_receiver_stream()
        self.rs232_interface.write("errs")
        # TODO: wait for sensor answer in an expected regex
