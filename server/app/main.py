import paho.mqtt.client as mqtt

import settings


def on_connect(client, userdata, flags, rc, properties=None):
    """The callback on CONNACK message from broker"""
    print(f"Connected with result code '{rc}'")
    client.subscribe("measurements")


def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    """The callback on SUBACK message from broker"""
    print(f"Subscribed: mid={mid} qos={granted_qos}")


def on_message(client, userdata, msg):
    """The callback on PUBLISH message from broker"""
    print(f"{msg.topic} {msg.payload}")


client = mqtt.Client(client_id="", userdata=None, protocol=mqtt.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message

# enable TLS for secure connection
client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
# set username and password
client.username_pw_set(settings.MQTT_IDENTIFIER, settings.MQTT_PASSWORD)
# connect on port 8883 (the default for MQTT)
client.connect(settings.MQTT_URL, port=8883, keepalive=60)


client.loop_forever()
