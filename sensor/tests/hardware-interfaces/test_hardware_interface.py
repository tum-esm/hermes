from os.path import dirname, abspath
import sys
import pytest

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import utils, hardware


@pytest.mark.hardware_interface
def test_hardware_interface() -> None:
    config = utils.ConfigInterface.read()
    hardware_interface = hardware.HardwareInterface(config=config)

    hardware_interface.check_errors()
    hardware_interface.teardown()
    hardware_interface.reinitialize(config)
    hardware_interface.teardown()
