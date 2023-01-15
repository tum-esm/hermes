import os
import time
from typing import Optional
from src import utils, custom_types
import re

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
ARDUINO_SCRIPT_PATH = os.path.join(PROJECT_DIR, "src", "heated_enclosure")

ARDUINO_CONFIG_TEMPLATE_PATH = os.path.join(ARDUINO_SCRIPT_PATH, "config.template.h")
ARDUINO_CONFIG_PATH = os.path.join(ARDUINO_SCRIPT_PATH, "config.h")

number_regex = r"\d+(\.\d+)?"
data_pattern = re.compile(
    f"version: {number_regex}; target: {number_regex}; allowed "
    + f"deviation: {number_regex}; measured: {number_regex}; "
    + "heater: (on|off); fan: (on|off)"
)


class HeatedEnclosureInterface:
    class DeviceFailure(Exception):
        """raised when the arduino either didn't answer for a while
        or when the code could not be uploaded to the device"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger = utils.Logger(origin="heated-enclosure")
        self.config = config

        self.logger.info("Compiling firmware of arduino")
        HeatedEnclosureInterface.compile_firmware(config)
        self.logger.info("Compiling firmware of arduino")
        HeatedEnclosureInterface.upload_firmware(config)
        self.logger.info("Arduino firmware successfully updated")

        time.sleep(0.5)

        self.serial_interface = utils.serial_interfaces.SerialOneDirectionalInterface(
            port=utils.Constants.WindSensor.serial_port,
            baudrate=9600,
        )
        self.data: Optional[custom_types.HeatedEnclosureData] = None

    def _update_current_values(self) -> None:
        new_messages = self.serial_interface.get_messages()
        now = round(time.time())
        for message in new_messages:
            if data_pattern.match(message) is not None:
                # determine the software currently used by the arduino
                # raise exception if software us too old
                used_software_version = message.split(";")[0].replace("version: ", "")
                if used_software_version != self.config.version:
                    raise HeatedEnclosureInterface.DeviceFailure(
                        f"Not running the expected software version. "
                        + f"Device uses {used_software_version}"
                    )

                message_items = message[len(used_software_version) + 11 :].split(";")
                target, allowed_deviation, measured = [
                    float(string)
                    for string in [
                        character
                        for character in message_items[:3]
                        if character.isnumeric()
                    ]
                ]
                heater_is_on, fan_is_on = [
                    "on" in string for string in message_items[3:]
                ]
                self.measurement = custom_types.HeatedEnclosureData(
                    target=target,
                    allowed_deviation=allowed_deviation,
                    measured=measured,
                    heater_is_on=heater_is_on,
                    fan_is_on=fan_is_on,
                    last_update_time=now,
                )

    def get_current_data(self) -> Optional[custom_types.HeatedEnclosureData]:
        self._update_current_values()
        return self.data

    @staticmethod
    def compile_firmware(config: custom_types.Config) -> None:
        with open(ARDUINO_CONFIG_TEMPLATE_PATH, "r") as f:
            config_content = f.read()

        for k, v in {
            "CODEBASE_VERSION": f'"{config.version}"',
            "TARGET_TEMPERATURE": str(config.heated_enclosure.target_temperature),
            "ALLOWED_TEMPERATURE_DEVIATION": str(
                config.heated_enclosure.allowed_deviation
            ),
        }.items():
            config_content = config_content.replace(f"%{k}%", v)

        with open(ARDUINO_CONFIG_PATH, "w") as f:
            f.write(config_content)

        utils.run_shell_command(
            f"arduino-cli compile --verbose "
            + f"--fqbn arduino:avr:nano:cpu=atmega328old "
            + f"--output-dir {ARDUINO_SCRIPT_PATH} "
            + f"--library {os.path.join(ARDUINO_SCRIPT_PATH, 'OneWire-2.3.7')} "
            + f"--library {os.path.join(ARDUINO_SCRIPT_PATH, 'DallasTemperature-3.9.0')} "
            + f"{ARDUINO_SCRIPT_PATH}"
        )

    @staticmethod
    def upload_firmware(config: custom_types.Config) -> None:
        utils.run_shell_command(
            f"arduino-cli upload --verbose "
            + "--fqbn arduino:avr:nano:cpu=atmega328old "
            + f"--port {config.heated_enclosure.device_path} "
            + f"--input-dir {ARDUINO_SCRIPT_PATH} "
            + f"{ARDUINO_SCRIPT_PATH}"
        )

    def check_errors(self) -> None:
        """raises the HeatedEnclosureInterface.DeviceFailure exception
        when the enclosure has not send any data in two minutes; logs a
        warning when the enclosure temperature exceeds 55°C
        """
        self._update_current_values()

        if self.data is None:
            self.logger.debug("waiting 6 seconds for data")
            time.sleep(6)

        self._update_current_values()

        if self.data is None:
            raise HeatedEnclosureInterface.DeviceFailure(
                "heated enclosure doesn't send any data"
            )

        if self.data.measured > 55:
            self.logger.warning(
                "high temperatures inside heated enclosure: "
                + f"{self.measurement.measured} °C",
                config=self.config,
            )

        if time.time() - self.data.last_update_time > 120:
            raise HeatedEnclosureInterface.DeviceFailure(
                "last heated enclosure data is older than two minutes"
            )
