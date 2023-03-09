from os.path import dirname, abspath
import sys
import time
from typing import Optional
import pytest

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import custom_types, utils, hardware


@pytest.mark.integration
def test_heated_enclosure(log_files: None) -> None:
    config = utils.ConfigInterface.read()
    heated_enclosure = hardware.HeatedEnclosureInterface(config)
    measurement: Optional[custom_types.HeatedEnclosureData]

    t1 = time.time()
    while True:
        measurement = heated_enclosure.get_current_measurement()
        if measurement is not None:
            break

        if (time.time() - t1) > 10:
            raise TimeoutError(
                "heated enclosure didn't send any data for 10 "
                + "seconds after successful initialization"
            )

    print(f"measurement = {measurement}")
    assert measurement.measured is not None, "temperature sensor not connected"

    heated_enclosure.teardown()
