from datetime import datetime
import json
import time
import pytest
from os.path import dirname, abspath, join
import sys

from ..pytest_fixtures import mqtt_client_environment, mqtt_sending_loop, log_files
from ..pytest_utils import expect_log_lines, wait_for_condition

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.log")
sys.path.append(PROJECT_DIR)

from src import interfaces, custom_types


@pytest.mark.ci
def test_mqtt_sending(mqtt_sending_loop: None, log_files: None) -> None:
    interfaces.SendingMQTTClient.check_errors()

    config = interfaces.ConfigInterface.read()

    dummy_measurement_message = custom_types.MQTTMeasurementMessageBody(
        timestamp=datetime.now().timestamp(),
        value=custom_types.CO2SensorData(raw=0.0, compensated=0.0, filtered=0.0),
    )
    interfaces.SendingMQTTClient.enqueue_message(
        config,
        dummy_measurement_message,
    )

    time.sleep(10)

    interfaces.SendingMQTTClient.check_errors()
