import os
import click
import utils
from src.utils import ConfigInterface

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(dirname(os.path.abspath(__file__)))))
ARDUINO_SCRIPT_PATH = os.path.join(PROJECT_DIR, "src", "heated_enclosure")

ARDUINO_CONFIG_TEMPLATE_PATH = os.path.join(ARDUINO_SCRIPT_PATH, "config.template.h")
ARDUINO_CONFIG_PATH = os.path.join(ARDUINO_SCRIPT_PATH, "config.h")


@click.command(help="List all connected arduino boards")
def compile_and_upload() -> None:

    with open(ARDUINO_CONFIG_TEMPLATE_PATH) as f:
        config_content = f.read()

    automation_config = ConfigInterface.read()

    for k, v in {
        "CODEBASE_VERSION": f'"{automation_config.version}"',
        "TARGET_TEMPERATURE": str(
            automation_config.heated_enclosure.target_temperature
        ),
        "ALLOWED_TEMPERATURE_DEVIATION": str(
            automation_config.heated_enclosure.allowed_deviation
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

    # TODO: add device path to command params
    device_path = "/dev/cu.usbserial-AB0O2OIH"

    utils.run_shell_command(
        f"arduino-cli upload --verbose "
        + "--fqbn arduino:avr:nano:cpu=atmega328old "
        + f"--port {device_path} "
        + f"--input-dir {ARDUINO_SCRIPT_PATH} "
        + f"{ARDUINO_SCRIPT_PATH}"
    )
