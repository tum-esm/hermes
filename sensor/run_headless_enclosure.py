import json
import os
import time
from src import utils, hardware, custom_types

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DST_FILE_PATH = os.path.join(PROJECT_DIR, "logs", "headless-enclosure-data.json")


def write_data(data: custom_types.HeatedEnclosureData) -> None:
    # read current list
    if os.path.exists(DST_FILE_PATH):
        with open(DST_FILE_PATH, "r") as f:
            current_list = json.load(f)
        assert isinstance(current_list, list), "dst file is not a list"
    else:
        current_list = []

    # append data and save new list
    new_list = current_list + [data.dict()]
    with open(DST_FILE_PATH, "w") as f:
        json.dump(new_list, f)


if __name__ == "__main__":
    config = utils.ConfigInterface.read()
    heated_enclosure = hardware.HeatedEnclosureInterface(config)

    print("sleeping 8 seconds to wait for data")
    time.sleep(8)

    last_update_time = None

    while True:
        current_data = heated_enclosure.get_current_data()
        assert current_data is not None, "enclosure doesn't send any data"

        if (last_update_time is None) or (
            last_update_time != current_data.last_update_time
        ):
            write_data(current_data)

        time.sleep(1)
