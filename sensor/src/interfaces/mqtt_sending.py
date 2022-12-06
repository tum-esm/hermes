import ssl
from paho.mqtt.client import Client
from src import custom_types


class SendingMQTTClient:
    def __init__(self, config: custom_types.Config) -> None:
        self.config = config
        self.client = Client(client_id=self.config.general.station_name)
        self.client.username_pw_set(config.mqtt.identifier, config.mqtt.password)
        self.client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED)
        self.client.connect(config.mqtt.url, port=config.mqtt.port, keepalive=60)

    # TODO: function to add status messages to queue file
    # TODO: function to add measurement messages to queue file
    # TODO: function to pick messages from the queue file and process them
