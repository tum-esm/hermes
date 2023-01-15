import time
from src import utils, hardware_interfaces


# TODO: log to file instead of print
# TODO: add timestamp to logs

if __name__ == "__main__":
    pass

    config = utils.ConfigInterface.read()
    heated_enclosure = hardware_interfaces.HeatedEnclosureInterface(config)

    print("sleeping 6 seconds to wait for data")
    time.sleep(6)

    last_update_time = None

    while True:
        current_data = heated_enclosure.get_current_data()
        assert current_data is not None, "enclosure doesn't send any data"

        if (last_update_time is None) or (
            last_update_time != current_data.last_update_time
        ):
            # TODO: add message to log stream
            pass

        time.sleep(1)

    # TODO: run heater enclosure interface
    # TODO: record measurement activity every 10 seconds in a dedicated file
