import json
import os
import time
from src import utils, hardware, custom_types

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DST_FILE_PATH = os.path.join(PROJECT_DIR, "logs", "headless-enclosure-data.log")


def write_data(data: custom_types.HeatedEnclosureData) -> None:
    with open(DST_FILE_PATH, "a") as f:
        f.write(f"{json.dumps(data.dict())}\n")


if __name__ == "__main__":
    config = utils.ConfigInterface.read()
    heated_enclosure = hardware.HeatedEnclosureInterface(config)

    print("sleeping 10 seconds to wait for data")
    time.sleep(10)

    last_update_time = None

    while True:
        current_data = heated_enclosure.get_current_data()
        assert current_data is not None, "enclosure doesn't send any data"

        if (last_update_time is None) or (
            last_update_time != current_data.last_update_time
        ):
            write_data(current_data)
            last_update_time = current_data.last_update_time

        time.sleep(1)
