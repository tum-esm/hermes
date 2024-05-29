from datetime import datetime
import json
import time
import pytest
from os.path import dirname, abspath, join
import sys
import deepdiff
from ..pytest_utils import expect_log_file_contents, wait_for_condition

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
LOG_FILE = join(
    PROJECT_DIR, "logs", "archive", datetime.now().strftime("%Y-%m-%d.log")
)
CONFIG_PATH = join(PROJECT_DIR, "config", "config.json")
sys.path.append(PROJECT_DIR)

from src import custom_types, utils, procedures

# this test has to run last because it fucks up something to mqtt tests afterwards won't work ...


@pytest.mark.remote_update
@pytest.mark.version_update
@pytest.mark.github_action
@pytest.mark.last
def test_mqtt_receiving(
    mqtt_client_environment: None,
    mqtt_data_files: None,
    log_files: None,
    sample_config: None,
) -> None:
    # -------------------------------------------------------------------------
    # 1. PUBLISH RETAINED CONFIG MESSAGE

    mqtt_connection = utils.MQTTConnection()
    mqtt_config = mqtt_connection.config
    mqtt_client = mqtt_connection.client

    config_topic = (
        f"{mqtt_config.mqtt_base_topic}configurations/{mqtt_config.station_identifier}"
    )
    print(f"config_topic = {config_topic}")
    sent_config_message = custom_types.MQTTConfigurationRequest(
        revision=1, configuration={"version": "0.1.0", "other_params": 30}
    )
    message_info = mqtt_client.publish(
        topic=config_topic,
        payload=json.dumps(sent_config_message.dict()),
        qos=1,
        retain=True,
    )
    wait_for_condition(
        is_successful=lambda: message_info.is_published(),
        timeout_message=f"message if mid {message_info.mid} could not be published",
    )
    mqtt_connection.teardown()
    assert not mqtt_client.is_connected(), "mqtt client is still connected"

    time.sleep(1)

    # -------------------------------------------------------------------------
    # 2. RECEIVE RETAINED CONFIG MESSAGE ON MESSAGING AGENT STARTUP

    with open(CONFIG_PATH) as f:
        config = custom_types.Config(**json.load(f))
        config.active_components.send_messages_over_mqtt = True
    procedures.MQTTAgent.init(config)

    time.sleep(5)

    procedures.MQTTAgent.check_errors()

    expect_log_file_contents(
        required_content_blocks=[
            f"message-communication   - INFO          - subscribed to topic {config_topic}",
            f"message-communication   - INFO          - received message on config topic: ",
            f"message-communication   - DEBUG         - put config message into the message queue",
        ]
    )

    # expect retained config message to be received
    received_config_message = procedures.MQTTAgent.get_config_message()
    assert received_config_message is not None

    differences = deepdiff.DeepDiff(
        received_config_message.dict(),
        sent_config_message.dict(),
    )
    print(f"differences = {differences}")
    assert differences == {}
