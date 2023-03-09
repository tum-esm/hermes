import json
import os
import time
from typing import Optional
from src import utils, custom_types

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
ARDUINO_SCRIPT_PATH = os.path.join(PROJECT_DIR, "src", "heated_enclosure")

ARDUINO_CONFIG_TEMPLATE_PATH = os.path.join(ARDUINO_SCRIPT_PATH, "config.template.h")
ARDUINO_CONFIG_PATH = os.path.join(ARDUINO_SCRIPT_PATH, "config.h")


class HeatedEnclosureInterface:
    class DeviceFailure(Exception):
        """raised when the arduino either didn't answer for a while
        or when the code could not be uploaded to the device"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger, self.config = utils.Logger(origin="heated-enclosure"), config
        self.logger.debug("Starting initialization")

        self.logger.debug("Finding arduino port")
        self.arduino_address = HeatedEnclosureInterface.get_arduino_address()
        self.logger.debug("Compiling firmware of arduino")
        HeatedEnclosureInterface.compile_firmware(config)
        self.logger.debug("Uploading firmware of arduino")
        HeatedEnclosureInterface.upload_firmware(self.arduino_address)
        self.logger.debug("Arduino firmware is now up to date")

        time.sleep(3)
        self.logger.debug("Opening serial communication port")
        self.serial_interface = utils.serial_interfaces.SerialOneDirectionalInterface(
            port=self.arduino_address, baudrate=9600
        )
        self.measurement: Optional[custom_types.HeatedEnclosureData] = None

        self.logger.debug("Finished initialization")

    def get_current_measurement(self) -> Optional[custom_types.HeatedEnclosureData]:
        new_messages = self.serial_interface.get_messages()
        for message in new_messages:
            message = message.strip("\n\r")
            try:
                parsed_message = custom_types.RawHeatedEnclosureData(
                    **json.loads(message)
                )
            except Exception as e:
                raise HeatedEnclosureInterface.DeviceFailure(
                    f"arduino sends unknown messages formats:"
                    + f" {repr(message)}, Exception: {e}"
                )

            if parsed_message.version != self.config.version:
                raise HeatedEnclosureInterface.DeviceFailure(
                    f"Not running the expected software version. "
                    + f"Device uses {parsed_message.version}"
                )

            self.measurement = custom_types.HeatedEnclosureData(
                target=parsed_message.target,
                allowed_deviation=parsed_message.allowed_deviation,
                measured=parsed_message.measured,
                heater_is_on=("on" in parsed_message.heater),
                fan_is_on=("on" in parsed_message.fan),
                last_update_time=round(time.time()),
            )

        return self.measurement

    @staticmethod
    def get_arduino_address() -> str:
        active_usb_ports = utils.run_shell_command('ls /dev | grep -i "ttyUSB"').split(
            "\n"
        )
        last_arduino_usb_port = utils.run_shell_command(
            'dmesg | grep -i "FTDI USB Serial Device converter now attached to" | tail -n 1'
        ).split(" ")[-1]
        if last_arduino_usb_port in active_usb_ports:
            return f"/dev/{last_arduino_usb_port}"
        else:
            raise HeatedEnclosureInterface.DeviceFailure("No Arduino found")

    @staticmethod
    def compile_firmware(config: custom_types.Config) -> None:
        """compile arduino software, static because this is also used by the CLI"""
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
    def upload_firmware(arduino_address: str) -> None:
        """upload the arduino software, static because this is also used by the CLI"""

        utils.run_shell_command(
            f"arduino-cli upload --verbose "
            + "--fqbn arduino:avr:nano:cpu=atmega328old "
            + f"--port {arduino_address} "
            + f"--input-dir {ARDUINO_SCRIPT_PATH} "
            + f"{ARDUINO_SCRIPT_PATH}"
        )

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.serial_interface.close()
