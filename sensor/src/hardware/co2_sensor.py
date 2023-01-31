import time
from typing import Optional
from src import utils, custom_types
import gpiozero
import gpiozero.pins.pigpio

number_regex = r"\d+(\.\d+)?"
startup_regex = (
    f"GMP343 - Version STD {number_regex}\\r\\n"
    + f"Copyright: Vaisala Oyj \\d{{4}} - \\d{{4}}"
)
measurement_regex = (
    f"Raw\\s*{number_regex} ppm; "
    + f"Comp\\.\\s*{number_regex} ppm; "
    + f"Filt\\.\\s*{number_regex} ppm"
)


CO2_SENSOR_POWER_PIN_OUT = 20
CO2_SENSOR_SERIAL_PORT = "/dev/ttySC0"


class CO2SensorInterface:
    class DeviceFailure(Exception):
        """raised when the CO2 probe "errs" command responds with an error"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger, self.config = utils.Logger(origin="co2-sensor"), config
        self.logger.info("Starting initialization")

        # power pin to power up/down wind sensor
        self.pin_factory = utils.get_gpio_pin_factory()
        self.power_pin = gpiozero.OutputDevice(
            pin=CO2_SENSOR_POWER_PIN_OUT, pin_factory=self.pin_factory
        )

        # serial connection to receive data from wind sensor
        self.rs232_interface = utils.serial_interfaces.SerialCO2SensorInterface(
            port=CO2_SENSOR_SERIAL_PORT
        )

        # turn the sensor off and on and set it to our default settings
        self._reset_sensor()

        self.logger.info("Finished initialization")

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
            "tc on",
            "lc on",
            "rhc off",
            "pc off",
            "oc off",
        ]:
            self.rs232_interface.send_command(default_setting)
            self.rs232_interface.wait_for_answer()

        # set default filters
        self.set_filter_setting(average=6)

    def set_filter_setting(
        self,
        median: int = 0,
        average: int = 10,
        smooth: int = 0,
        linear: bool = True,
    ) -> None:
        """update the filter settings on the CO2 probe"""

        # TODO: construct a few opinionated measurement setups

        assert (
            average >= 0 and average <= 60
        ), "invalid calibration setting, average not in [0, 60]"
        assert (
            smooth >= 0 and smooth <= 255
        ), "invalid calibration setting, smooth not in [0, 255]"
        assert (
            median >= 0 and median <= 13
        ), "invalid calibration setting, median not in [0, 13]"

        self.rs232_interface.flush_receiver_stream()

        self.rs232_interface.send_command(f"average {average}")
        self.rs232_interface.wait_for_answer()

        self.rs232_interface.send_command(f"smooth {smooth}")
        self.rs232_interface.wait_for_answer()

        self.rs232_interface.send_command(f"median {median}")
        self.rs232_interface.wait_for_answer()

        self.rs232_interface.send_command(f"linear {'on' if linear else 'off'}")
        self.rs232_interface.wait_for_answer()

        self.logger.info(
            f"Updating filter settings (average = {average}, smooth"
            + f" = {smooth}, median = {median}, linear = {linear})"
        )

    def set_calibration_values(
        self,
        pressure: Optional[float] = None,
        humidity: Optional[float] = None,
        oxygen: Optional[float] = None,
    ) -> None:
        """
        update pressure, humidity, and oxygen values in sensor
        for its internal calibration.

        if any of these value is None, then the calibration is
        turned off, otherwise it is switched on automatically.

        the internal temperature calibration is enabled by de-
        fault and uses the built-in temperature sensor.
        """

        self.rs232_interface.flush_receiver_stream()

        if pressure is None:
            self.rs232_interface.send_command(f"pc off")
            self.rs232_interface.wait_for_answer()
        else:
            assert (
                700 <= pressure <= 1300
            ), f"invalid pressure ({pressure} not in [700, 1300])"
            self.rs232_interface.send_command(f"pc on")
            self.rs232_interface.wait_for_answer()
            self.rs232_interface.send_command(f"p {round(pressure, 2)}")
            self.rs232_interface.wait_for_answer()

        if humidity is None:
            self.rs232_interface.send_command(f"rhc off")
            self.rs232_interface.wait_for_answer()
        else:
            assert (
                0 <= humidity <= 100
            ), f"invalid humidity ({humidity} not in [0, 100])"
            self.rs232_interface.send_command(f"rhc on")
            self.rs232_interface.wait_for_answer()
            self.rs232_interface.send_command(f"rh {round(humidity, 2)}")
            self.rs232_interface.wait_for_answer()

        if oxygen is None:
            self.rs232_interface.send_command(f"oc off")
            self.rs232_interface.wait_for_answer()
        else:
            assert 0 <= oxygen <= 100, f"invalid oxygen ({oxygen} not in [0, 100])"
            self.rs232_interface.send_command(f"oc on")
            self.rs232_interface.wait_for_answer()
            self.rs232_interface.send_command(f"o {round(oxygen, 2)}")
            self.rs232_interface.wait_for_answer()

        self.logger.info(
            f"updating calibration values (pressure = {pressure}, "
            + f"humidity = {humidity}, oxygen = {oxygen})"
        )

    def get_current_concentration(self) -> custom_types.CO2SensorData:
        """get the current concentration value from the CO2 probe"""
        answer: str
        try:
            self.rs232_interface.flush_receiver_stream()
            self.rs232_interface.send_command("send")
            answer = self.rs232_interface.wait_for_answer(expected_regex=measurement_regex)
        except TimeoutError:
            self.rs232_interface.flush_receiver_stream()
            self.rs232_interface.send_command("send")
            answer = self.rs232_interface.wait_for_answer(expected_regex=measurement_regex)

        for s in [" ", "Raw", "ppm", "Comp.", "Filt.", ">", "\r\n"]:
            answer = answer.replace(s, "")
        raw_value_string, comp_value_string, filt_value_string = answer.split(";")
        return custom_types.CO2SensorData(
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

    def start_calibration_sampling(self) -> None:
        self.rs232_interface.flush_receiver_stream()
        self.rs232_interface.send_command("CALIB ON")
        self.rs232_interface.wait_for_answer()

    def stop_calibration_sampling(self) -> None:
        self.rs232_interface.flush_receiver_stream()
        self.rs232_interface.send_command("CALIB OFF")
        self.rs232_interface.wait_for_answer()

    def check_errors(self) -> None:
        """checks whether the CO2 probe reports any errors. Possibly raises
        the CO2SensorInterface.DeviceFailure exception"""
        self.rs232_interface.flush_receiver_stream()
        self.rs232_interface.send_command("errs")
        answer = self._format_raw_answer(self.rs232_interface.wait_for_answer())

        if not ("OK: No errors detected" in answer):
            raise CO2SensorInterface.DeviceFailure(answer)

        self.logger.info("sensor doesn't report any errors")

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.power_pin.off()
        self.pin_factory.close()

        # I don't know why this is needed sometimes, just to make sure
        utils.run_shell_command(f"pigs w {CO2_SENSOR_POWER_PIN_OUT} 0")
