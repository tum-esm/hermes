import os
import click
import utils

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(dirname(os.path.abspath(__file__)))))
ARDUINO_SCRIPT_PATH = os.path.join(PROJECT_DIR, "src", "heated_enclosure")


@click.command(help="List all connected arduino boards")
def compile_and_upload() -> None:
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
