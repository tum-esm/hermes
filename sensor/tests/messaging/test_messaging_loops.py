import time
import pytest
from os.path import dirname, abspath
import sys

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, procedures


@pytest.mark.version_update
@pytest.mark.ci
def test_messaging_loops_with_sending(
    mqtt_client_environment: None,
    mqtt_data_files: None,
    log_files: None,
    sample_config: None,
) -> None:
    config = utils.ConfigInterface.read()
    config.active_components.send_messages_over_mqtt = True

    procedures.MQTTAgent.init(config)
    procedures.MQTTAgent.check_errors()

    time.sleep(4)

    procedures.MQTTAgent.check_errors()
    procedures.MQTTAgent.deinit()


@pytest.mark.version_update
@pytest.mark.ci
def test_messaging_loops_without_sending(
    mqtt_client_environment: None,
    mqtt_data_files: None,
    log_files: None,
    sample_config: None,
) -> None:
    config = utils.ConfigInterface.read()
    config.active_components.send_messages_over_mqtt = False

    procedures.MQTTAgent.init(config)
    procedures.MQTTAgent.check_errors()

    time.sleep(4)

    procedures.MQTTAgent.check_errors()
    procedures.MQTTAgent.deinit()
