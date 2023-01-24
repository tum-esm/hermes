from datetime import datetime
import json
import os
import time
from typing import Optional
from src import utils, hardware, custom_types
import filelock

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DST_FILE_PATH = os.path.join(PROJECT_DIR, "logs", "headless-enclosure-data.log")
LOCK_FILE_PATH = os.path.join(PROJECT_DIR, "logs", "headless-enclosure-data.lock")
lock = filelock.FileLock(LOCK_FILE_PATH, timeout=2)


def write_data(
    enclosure_data: custom_types.HeatedEnclosureData,
    mainboard_sensor_data: custom_types.MainboardSensorData,
) -> None:
    with open(DST_FILE_PATH, "a") as f:
        merged_dict = {
            **enclosure_data.dict(),
            **mainboard_sensor_data.dict(),
        }
        f.write(f"{json.dumps(merged_dict)}\n")


if __name__ == "__main__":
    try:
        with lock:
            print(f"acquired lock with PID {os.getpid()} at {datetime.now()}")
            config = utils.ConfigInterface.read()
            heated_enclosure = hardware.HeatedEnclosureInterface(config)
            mainboard_sensor = hardware.MainboardSensorInterface(config)

            print("sleeping 10 seconds to wait for data")
            time.sleep(10)

            last_update_time: Optional[float] = None

            while True:
                current_data = heated_enclosure.get_current_data()
                assert current_data is not None, "enclosure doesn't send any data"

                if last_update_time != current_data.last_update_time:
                    write_data(current_data, mainboard_sensor.get_system_data())
                    last_update_time = current_data.last_update_time

                # cycle power on USB ports if Arduino hast answered for 2 minutes
                if (time.time() - last_update_time) > 120:
                    heated_enclosure.teardown()
                    hardware.USBPortInterface.toggle_usb_power()
                    heated_enclosure = hardware.HeatedEnclosureInterface(config)

                time.sleep(1)
    except filelock.Timeout:
        print(f"could not acquire lock from pid {os.getpid()}")
