import time
import pytest
from ..pytest_fixtures import (
    mqtt_client_environment,
    mqtt_data_files,
    log_files,
    sample_config,
)
from os.path import dirname, abspath
import sys

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, procedures


@pytest.mark.config_update
@pytest.mark.ci
def test_messaging_loops_with_sending(
    mqtt_client_environment: None,
    mqtt_data_files: None,
    log_files: None,
    sample_config: None,
) -> None:
    config = utils.ConfigInterface.read()
    config.active_components.mqtt_communication = True

    procedures.MessagingAgent.init(config)
    procedures.MessagingAgent.check_errors()

    time.sleep(8)

    procedures.MessagingAgent.check_errors()
    procedures.MessagingAgent.deinit()


@pytest.mark.config_update
@pytest.mark.ci
def test_messaging_loops_without_sending(
    mqtt_client_environment: None,
    mqtt_data_files: None,
    log_files: None,
    sample_config: None,
) -> None:
    config = utils.ConfigInterface.read()
    config.active_components.mqtt_communication = False

    procedures.MessagingAgent.init(config)
    procedures.MessagingAgent.check_errors()

    time.sleep(8)

    procedures.MessagingAgent.check_errors()
    procedures.MessagingAgent.deinit()
