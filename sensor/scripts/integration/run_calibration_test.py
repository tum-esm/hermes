import os
import sys
import time

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(PROJECT_DIR)

from src import utils, hardware, procedures

config = utils.ConfigInterface.read()
logger = utils.Logger("main", print_to_console=True, write_to_file=False)
hardware_interface = hardware.HardwareInterface(config, testing=True)
calibration_procedure = procedures.CalibrationProcedure(
    config, hardware_interface, testing=True
)

while hardware_interface.co2_sensor.get_current_concentration().raw < 10:
    logger.info("waiting for CO2 sensor to deliver valid data")
    time.sleep(1)

try:
    calibration_procedure.run()
finally:
    logger.info("tearing down hardware")
    hardware_interface.teardown()
