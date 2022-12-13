import json
import time
import pytest
from os.path import dirname, abspath, join
import sys

from ..pytest_fixtures import mqtt_client_environment, log_files
from ..pytest_utils import expect_log_lines, wait_for_condition

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.log")
sys.path.append(PROJECT_DIR)

from src import utils, interfaces, custom_types


@pytest.mark.ci
def test_mqtt_sending(mqtt_client_environment: None, log_files: None) -> None:
    config = interfaces.ConfigInterface.read()
    interfaces.SendingMQTTClient.init_sending_loop_process()

    dummy_measurement_message = custom_types.MQTTMeasurementMessageBody(
        timestamp=time.time(),
        value=custom_types.CO2SensorData(raw=0.0, compensated=0.0, filtered=0.0),
    )
    interfaces.SendingMQTTClient.enqueue_message(
        config,
        dummy_measurement_message,
    )

    time.sleep(10)
