import multiprocessing
import queue
import time
import pytest
from os.path import dirname, abspath
import sys

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import custom_types, utils, procedures


@pytest.mark.remote_update
@pytest.mark.github_action
def test_messaging_loops_function(
    mqtt_client_environment: None,
    mqtt_data_files: None,
    log_files: None,
    sample_config: None,
) -> None:
    """run the communication loop function in main thread"""
    config = utils.ConfigInterface.read()
    config_request_queue: queue.Queue[
        custom_types.MQTTConfigurationRequest
    ] = multiprocessing.Queue()
    procedures.MQTTAgent.communication_loop(
        config, config_request_queue, end_after_one_loop=True
    )


@pytest.mark.remote_update
@pytest.mark.github_action
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


@pytest.mark.remote_update
@pytest.mark.github_action
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
