import time
from typing import Optional
from src import utils, custom_types
import gpiozero
import gpiozero.pins.pigpio

NUMBER_REGEX = r"\d+\.\d+"
STARTUP_REGEX = (
    f"GMP343 - Version STD {NUMBER_REGEX}\\r\\n"
    + f"Copyright: Vaisala Oyj \\d{{4}} - \\d{{4}}"
)
MEASUREMENT_REGEX = (
    r"\d+\.\d+\s+"  # raw
    + r"\d+\.\d+\s+"  # compensated
    + r"\d+\.\d+\s+"  # compensated + filtered
    + r"\d+\.\d+\s+"  # temperature
    + r"\(R C C\+F T\)"
)

CO2_SENSOR_POWER_PIN_OUT = 20
CO2_SENSOR_SERIAL_PORT = "/dev/ttySC0"


class CO2SensorInterface:
    class DeviceFailure(Exception):
        """raised when the CO2 probe "errs" command responds with an error"""

    def __init__(
        self,
        config: custom_types.Config,
        testing: bool = False,
    ) -> None:
        self.logger = utils.Logger(
            origin="co2-sensor",
            print_to_console=testing,
            write_to_file=(not testing),
        )
        self.config = config
        self.logger.info("Starting initialization")
        self.last_powerup_time: float = time.time()

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
        self.last_powerup_time = time.time()
        self.rs232_interface.wait_for_answer(expected_regex=STARTUP_REGEX)

        self.logger.debug("sending default settings")
        for default_setting in [
            "echo off",  # do not output received strings
            "range 1",  # measuring from 0 to 1000 ppm
            'form CO2RAWUC CO2RAW CO2 T " (R C C+F T)"',
            "tc on",  # temperature compensation
            "lc off",  # line correction
            "rhc off",  # relative humidity compensation
            "pc off",  # pressure compensation
            "oc off",  # oxygen compensation
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
            f"updating filter settings (average = {average}, smooth"
            + f" = {smooth}, median = {median}, linear = {linear})"
        )

    def set_compensation_values(
        self,
        pressure: Optional[float] = None,
        humidity: Optional[float] = None,
        oxygen: Optional[float] = None,
    ) -> None:
        """
        update pressure, humidity, and oxygen values in sensor
        for its internal compensation.

        if any of these value is None, then the compensation is
        turned off, otherwise it is switched on automatically.

        the internal temperature compensation is enabled by de-
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
            f"updating compensation values (pressure = {pressure}, "
            + f"humidity = {humidity}, oxygen = {oxygen})"
        )

    def _get_current_sensor_data(self) -> tuple[float, float, float, float]:
        """get the current data from the CO2 probe
        tuple[co2rawuc, co2raw, co2, t]"""
        self.rs232_interface.flush_receiver_stream()

        request_time = time.time()
        self.rs232_interface.send_command("send")
        answer = self.rs232_interface.wait_for_answer(
            expected_regex=MEASUREMENT_REGEX, timeout=30
        )
        answer_delay = round(time.time() - request_time, 3)
        if answer_delay > 6:
            self.logger.warning(
                f"sensor took a long time to answer ({answer_delay}s)",
                config=self.config,
            )
        xs = [s for s in answer.replace("\t", " ").split(" ") if len(s) > 0]
        return float(xs[0]), float(xs[1]), float(xs[2]), float(xs[3])

    def get_current_concentration(self) -> custom_types.CO2SensorData:
        """get the current concentration value from the CO2 probe"""
        sensor_data = self._get_current_sensor_data()
        return custom_types.CO2SensorData(
            raw=sensor_data[0], compensated=sensor_data[1], filtered=sensor_data[2]
        )

    def get_current_chamber_temperature(self) -> float:
        """get the current concentration value from the CO2 probe"""
        sensor_data = self._get_current_sensor_data()
        return sensor_data[3]

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
        self.pin_factory.close()

        # I don't know why this is needed sometimes, just to make sure
        utils.run_shell_command(f"pigs w {CO2_SENSOR_POWER_PIN_OUT} 0")
