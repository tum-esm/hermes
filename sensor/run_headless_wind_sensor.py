from datetime import datetime
import json
import os
import time
from typing import Union
from src import utils, hardware, custom_types
import filelock

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DST_FILE_PATH = os.path.join(PROJECT_DIR, "logs", "headless-wind-sensor-data.log")
LOCK_FILE_PATH = os.path.join(PROJECT_DIR, "logs", "headless-wind-sensor-data.lock")
lock = filelock.FileLock(LOCK_FILE_PATH, timeout=2)


def write_data(
    data: Union[custom_types.WindSensorData, custom_types.WindSensorStatus]
) -> None:
    with open(DST_FILE_PATH, "a") as f:
        f.write(f"{json.dumps(data.dict())}\n")


if __name__ == "__main__":
    try:
        with lock:
            print(f"acquired lock with PID {os.getpid()} at {datetime.now()}")
            config = utils.ConfigInterface.read()
            wind_sensor = hardware.WindSensorInterface(config)

            print("sleeping 2 seconds to wait for data")
            time.sleep(2)

            last_data_update_time = None
            last_status_update_time = None

            while True:
                current_data = wind_sensor.get_current_wind_measurement()
                if current_data is not None:
                    if current_data.last_update_time != last_data_update_time:
                        write_data(current_data)
                        last_data_update_time = current_data.last_update_time

                current_status = wind_sensor.get_current_device_status()
                if current_status is not None:
                    if current_status.last_update_time != last_status_update_time:
                        write_data(current_status)
                        last_status_update_time = current_status.last_update_time

                time.sleep(1)
    except filelock.Timeout:
        print(f"could not acquire lock from pid {os.getpid()}")
