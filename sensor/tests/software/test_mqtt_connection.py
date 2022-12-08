from fixtures import provide_mqtt_broker
from os.path import dirname, abspath

import sys

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils


def test_mqtt_receiving(provide_mqtt_broker) -> None:
    mqtt_client, mqtt_config = utils.mqtt.get_mqtt_client()

    # testing whether config variables have been loaded correctly
    assert mqtt_config.station_identifier == "test_identifier"
    assert mqtt_config.mqtt_username == "test_username"
    assert mqtt_config.mqtt_password == "test_password"
