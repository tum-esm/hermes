import json
import time
from paho.mqtt.client import Client
import ssl
from src import interfaces

config = interfaces.ConfigInterface.read()
client = Client(client_id="test-sender")
client.username_pw_set(config.mqtt.identifier, config.mqtt.password)
client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED)
client.connect(config.mqtt.url, port=config.mqtt.port, keepalive=60)

i = 0
while True:
    client.publish(
        config.mqtt.base_topic + "/initial-setup-test",
        json.dumps({"type": "text", "body": f"iteration {i}"}),
    )
    print(f"published message {i}")
    i += 1
    time.sleep(2)
