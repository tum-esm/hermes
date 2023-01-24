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


def write_data(data: custom_types.HeatedEnclosureData) -> None:
    with open(DST_FILE_PATH, "a") as f:
        f.write(f"{json.dumps(data.dict())}\n")


if __name__ == "__main__":
    try:
        with lock:
            print(f"acquired lock with PID {os.getpid()} at {datetime.now()}")
            config = utils.ConfigInterface.read()
            heated_enclosure = hardware.HeatedEnclosureInterface(config)

            print("sleeping 10 seconds to wait for data")
            time.sleep(10)

            last_update_time: Optional[float] = None

            while True:
                current_data = heated_enclosure.get_current_data()
                assert current_data is not None, "enclosure doesn't send any data"

                if last_update_time != current_data.last_update_time:
                    write_data(current_data)
                    last_update_time = current_data.last_update_time

                # cycle power on USB ports if Arduino hast answered for 2 minutes
                if (time.time() - last_update_time) > 120:
                    heated_enclosure.teardown()
                    hardware.USBPortInterface.toggle_usb_power()
                    heated_enclosure = hardware.HeatedEnclosureInterface(config)

                time.sleep(1)
    except filelock.Timeout:
        print(f"could not acquire lock from pid {os.getpid()}")
