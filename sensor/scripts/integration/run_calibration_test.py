import os
import sys

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(PROJECT_DIR)

from src import utils, hardware, procedures

config = utils.ConfigInterface.read()

hardware_interface = hardware.HardwareInterface(config, testing=True)
calibration_procedure = procedures.CalibrationProcedure(
    config, hardware_interface, testing=True
)
