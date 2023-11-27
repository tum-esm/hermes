import time
from typing import Literal, Optional
from src import utils, custom_types
import gpiozero
import gpiozero.pins.pigpio

times_REGEX = r"\d+\.\d+"
STARTUP_REGEX = (
    f"GMP343 - Version STD {times_REGEX}\\r\\n"
    + f"Copyright: Vaisala Oyj \\d{{4}} - \\d{{4}}"
)
CO2_MEASUREMENT_REGEX = (
    r"\d+\.\d+\s+"  # raw
    + r"\d+\.\d+\s+"  # compensated
    + r"\d+\.\d+\s+"  # compensated + filtered
    + r"\d+\.\d+\s+"  # temperature
    + r"\(R C C\+F T\)"
)

CO2_SENSOR_POWER_PIN_OUT = 20
CO2_SENSOR_SERIAL_PORT = "/dev/ttySC0"


class CO2SensorInterface:
    class CommunicationError(Exception):
        """raised when the CO2 communication fails"""

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

        # power pin to power up/down CO2 sensor
        self.pin_factory = utils.get_gpio_pin_factory()
        self.power_pin = gpiozero.OutputDevice(
            pin=CO2_SENSOR_POWER_PIN_OUT, pin_factory=self.pin_factory
        )

        # serial connection to receive data from CO2 sensor
        self.serial_interface = utils.serial_interfaces.SerialCO2SensorInterface(
            port=CO2_SENSOR_SERIAL_PORT
        )

        # turn the sensor off and on and set it to our default settings
        self._reset_sensor()

        self.logger.info("finished initialization")

    # set functions

    def set_compensation_values(self, pressure: float, humidity: float) -> None:
        """
        update pressure, humidity in sensor
        for its internal compensation.

        the internal temperature compensation is enabled by de-
        fault and uses the built-in temperature sensor.
        """

        assert 0 <= humidity <= 100, f"invalid humidity ({humidity} not in [0, 100])"
        assert (
            700 <= pressure <= 1300
        ), f"invalid pressure ({pressure} not in [700, 1300])"

        self._set_sensor_parameter(parameter="rh", value=round(humidity, 2))
        self._set_sensor_parameter(parameter="p", value=round(pressure, 2))

        self.logger.info(
            f"updated compensation values: pressure = {pressure}, "
            + f"humidity = {humidity}"
        )

    def set_filter_setting(
        self,
        median: int = 0,
        average: int = 10,
        smooth: int = 0,
        linear: bool = True,
    ) -> None:
        """update the filter settings on the CO2 probe"""

        assert (
            average >= 0 and average <= 60
        ), "invalid calibration setting, average not in [0, 60]"
        assert (
            smooth >= 0 and smooth <= 255
        ), "invalid calibration setting, smooth not in [0, 255]"
        assert (
            median >= 0 and median <= 13
        ), "invalid calibration setting, median not in [0, 13]"

        self._set_sensor_parameter(parameter="average", value=average)
        self._set_sensor_parameter(parameter="smooth", value=smooth)
        self._set_sensor_parameter(parameter="median", value=median)

        self.logger.info(
            f"updating filter settings (average = {average}, smooth"
            + f" = {smooth}, median = {median})"
        )

    # get functions

    def get_current_concentration(
        self, pressure: Optional[float] = None, humidity: Optional[float] = None
    ) -> custom_types.CO2SensorData:
        """get the latest concentration and chamber temperature from the CO2 probe"""

        # request data from CO2 sensor
        try:
            # set compensation values if provided
            if (humidity is not None) and (pressure is not None):
                self.set_compensation_values(pressure=pressure, humidity=humidity)

            answer = self._request_measurement_data()

            xs = [s for s in answer.replace("\t", " ").split(" ") if len(s) > 0]
            sensor_data = float(xs[0]), float(xs[1]), float(xs[2]), float(xs[3])

        except Exception as e:
            self.logger.exception(
                e,
                label="exception during CO2 sensor measurement request - restarting sensor",
                config=self.config,
            )
            self._reset_sensor()
            sensor_data = (0.0, 0.0, 0.0, 0.0)

        return custom_types.CO2SensorData(
            raw=sensor_data[0],
            compensated=sensor_data[1],
            filtered=sensor_data[2],
            temperature=sensor_data[3],
        )

    def get_param_info(self) -> str:
        """runs the "param" command to get a full sensor parameter report"""
        try:
            return self._send_command_to_sensor("param")
        except Exception:
            self._reset_sensor()
            return self._send_command_to_sensor("param")

    def get_device_info(self) -> str:
        """runs the "??" command to get a full sensor parameter report"""
        try:
            return self._send_command_to_sensor("??")
        except Exception:
            self._reset_sensor()
            return self._send_command_to_sensor("??")

    def get_correction_info(self) -> str:
        """runs the "corr" command to get a full sensor parameter report"""
        try:
            return self._send_command_to_sensor("corr")
        except Exception:
            self._reset_sensor()
            return self._send_command_to_sensor("corr")

    # utility functions

    def _send_command_to_sensor(
        self,
        command: str,
        expected_regex: str = r".*\>.*",
        timeout: float = 8,
    ) -> str:
        """Allows to send a full text command to the GMP343 CO2 Sensor.
        Please refer to the user manual for valid commands."""

        answer = self.serial_interface.send_command(command)

        if answer[0] == "success":
            return self._format_raw_answer(answer[1])
        else:
            raise self.CommunicationError(
                f"Could not send command to sensor. Command: {command}. Sensor answer: {answer[1]}"
            )

    def _set_sensor_parameter(
        self,
        parameter: str,
        value: float,
        expected_regex: str = r".*\>.*",
        timeout: float = 8,
    ) -> str:
        """Allows to change a parameter in the GMP343 CO2 Sensor.
        The sensor response is checked. In case of a uncompleted
        request the parameter is sent again to finish to parameter
        change.
        In case the sensor does not respond a timeout will retrigger
        the request to the sensor.
        At success the sensor answer is returned.
        In all other cases a Communication Error is raised.
        """
        command = f"{parameter} {value}"

        answer = self.serial_interface.send_command(
            message=command, expected_regex=expected_regex, timeout=timeout
        )

        if answer[0] == "success":
            return answer[1]

        if answer[0] == "uncomplete":
            # command was sent uncomplete. sensor asked to set value.
            self.logger.warning(
                f"command was sent uncomplete. resending value: {value}"
            )
            answer = self.serial_interface.send_command(
                message=str(value), expected_regex=expected_regex, timeout=timeout
            )
            if answer[0] == "success":
                self.logger.info("resending value was successful")
                return answer[1]
            else:
                raise self.CommunicationError(
                    f"resend failed after uncomplete. Sensor answer: {answer[1]}"
                )

        if answer[0] == "timeout":
            # retry sending command
            self.logger.warning(
                f"sent sensor command timed out. resending command: {command}"
            )
            answer = self.serial_interface.send_command(
                message=command, expected_regex=expected_regex, timeout=timeout
            )

            if answer[0] == "success":
                self.logger.info("resending command was successful")
                return answer[1]
            else:
                raise self.CommunicationError(
                    f"resend failed after timeout. Command: {command}. Sensor answer: {answer[1]}"
                )

    def _request_measurement_data(self) -> str:
        """Requests the latest measurement from the GMP343 CO2 Sensor.
        If the first request runs into a timeout another request is sent.
        At success the sensor answer is returned.
        In all other cases a Communication Error is raised.
        """

        answer = self.serial_interface.send_command(
            "send", expected_regex=CO2_MEASUREMENT_REGEX, timeout=30
        )

        if answer[0] == "success":
            return answer[1]
        elif answer[0] == "timeout":
            # retry sending command
            self.logger.warning(
                "sensor answer for measurement request timed out. resending request."
            )
            answer = self.serial_interface.send_command(
                "send", expected_regex=CO2_MEASUREMENT_REGEX, timeout=30
            )

            if answer[0] == "success":
                self.logger.info("resending value was successful")
                return answer[1]
            else:
                raise self.CommunicationError(
                    f"resend failed after timeout. Sensor answer: {answer[1]}"
                )
        else:
            self.logger.warning("requesting measurement failed")
            raise self.CommunicationError(f"Uncomplete. Sensor answer: {answer[1]}")

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

    def _reset_sensor(self) -> None:
        """reset the sensors default settings by turning it off and on and
        sending the initial settings again"""

        self.logger.info("initializing the sensor with measurement settings")

        self.logger.debug("powering down sensor")
        self.power_pin.off()
        time.sleep(1)

        self.logger.debug("powering up sensor")
        self.serial_interface.flush_receiver_stream()
        self.power_pin.on()
        self.last_powerup_time = time.time()
        self.serial_interface.wait_for_answer(expected_regex=STARTUP_REGEX, timeout=10)

        self.logger.debug("sending measurement settings")

        self._send_command_to_sensor(command="echo off")
        time.sleep(0.1)
        self._set_sensor_parameter(parameter="range", value=1)
        time.sleep(0.1)
        self._send_command_to_sensor(command="heat on")
        time.sleep(0.1)
        self._send_command_to_sensor(command="linear on")
        time.sleep(0.1)
        self._send_command_to_sensor(
            command='form CO2RAWUC CO2RAW CO2 T " (R C C+F T)"'
        )
        time.sleep(0.1)
        self._send_command_to_sensor(command="tc on")
        time.sleep(0.1)
        self._send_command_to_sensor(command="rhc on")
        time.sleep(0.1)
        self._send_command_to_sensor(command="pc on")
        time.sleep(0.1)
        self._send_command_to_sensor(command="oc on")
        time.sleep(0.1)

        # set filter setting
        self.set_filter_setting(
            average=self.config.measurement.timing.seconds_per_measurement
        )

    def check_errors(self) -> None:
        """checks whether the CO2 probe reports any errors. Possibly raises
        the CO2SensorInterface.CommunicationError exception"""
        answer = self._send_command_to_sensor("errs")

        if not ("OK: No errors detected." in answer):
            self.logger.info("the CO2 sensor error check failed. Performing restart.")
            self._reset_sensor()

        self.logger.info("the CO2 sensor check doesn't report any errors")

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.pin_factory.close()

        # I don't know why this is needed sometimes, just to make sure
        utils.run_shell_command(f"pigs w {CO2_SENSOR_POWER_PIN_OUT} 0")
