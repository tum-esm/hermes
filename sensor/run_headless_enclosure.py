from datetime import datetime
import json
import os
import time
from typing import Any, Optional
import filelock
from src import utils, hardware


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DST_FILE_PATH = os.path.join(PROJECT_DIR, "logs", "headless-enclosure-data.log")
LOCK_FILE_PATH = os.path.join(PROJECT_DIR, "logs", "headless-enclosure-data.lock")
lock = filelock.FileLock(LOCK_FILE_PATH, timeout=2)


def write_data(data: dict[Any, Any]) -> None:
    with open(DST_FILE_PATH, "a") as f:
        f.write(f"{json.dumps(data)}\n")


if __name__ == "__main__":
    try:
        with lock:
            print(f"acquired lock with PID {os.getpid()} at {datetime.now()}")
            config = utils.ConfigInterface.read()
            heated_enclosure = hardware.HeatedEnclosureInterface(config)
            mainboard_sensor = hardware.BME280SensorInterface(
                config, variant="mainboard"
            )
            air_inlet_bme280_sensor = hardware.BME280SensorInterface(
                config, variant="air-inlet"
            )

            print("sleeping 10 seconds to wait for data")
            time.sleep(10)

            last_update_time: Optional[float] = None

            while True:
                current_data = heated_enclosure.get_current_measurement()
                assert current_data is not None, "enclosure doesn't send any data"

                if last_update_time != current_data.last_update_time:
                    air_inlet_bme280_data = air_inlet_bme280_sensor.get_data()
                    mainboard_sensor_data = mainboard_sensor.get_data()
                    write_data(
                        {
                            "enclosure": current_data.dict(),
                            "air_inlet_bme280": air_inlet_bme280_data.dict(),
                            "mainboard": mainboard_sensor_data.dict(),
                        }
                    )
                    last_update_time = current_data.last_update_time

                # cycle power on USB ports if Arduino hast answered for 2 minutes
                assert last_update_time is not None
                if (time.time() - last_update_time) > 120:
                    write_data({"hard_reset_time": time.time()})
                    print("performing hard reset")
                    heated_enclosure.teardown()
                    hardware.USBPortInterface.toggle_usb_power()
                    heated_enclosure = hardware.HeatedEnclosureInterface(config)
                    print("sleeping 10 seconds to wait for data")
                    time.sleep(10)

                time.sleep(1)
    except filelock.Timeout:
        print(f"could not acquire lock from pid {os.getpid()}")
