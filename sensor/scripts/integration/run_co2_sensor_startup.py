import os
import sys
import time
import gpiozero

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, hardware_interfaces


try:
    config = hardware_interfaces.ConfigInterface.read()
    interface = hardware_interfaces.co2_sensor.RS232Interface()
    sensor_power_pin = gpiozero.OutputDevice(
        pin=utils.Constants.co2_sensor.pin_power_out
    )

    sensor_power_pin.off()
    time.sleep(1)

    sensor_power_pin.on()
    interface.serial_interface.write("ZZZZZZZZZZZZ".encode("utf-8"))
    interface.serial_interface.flush()
    time.sleep(5)

    answer = interface.serial_interface.read_all().decode(
        encoding="cp1252", errors="ignore"
    )
    print(answer)
finally:
    os.system(f"pigs w {utils.Constants.pump.pin_control_out} 0")
