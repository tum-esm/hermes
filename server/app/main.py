import paho.mqtt.client as mqtt

import settings


def on_connect(client, userdata, flags, reason_code, properties=None):
    """The callback on CONNACK message from broker.

    Reason codes:
    -------------------------------
    0   connection successful
    1   refused, incorrect protocol version
    2   refused, invalid client identifier
    3   refused, server unavailable
    4   refused, bad username or password
    5   refused, not authorized

    also see the official documentation at
    https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901031
    from https://mqtt.org/mqtt-specification/ which lists different reason codes?

    """
    print(f"[CONNECTED] reason_code={reason_code}")
    # TODO quit if unsuccessful > set flag, stop in main loop
    # TODO need mechanism to block publishing before successful CONNACK
    # e.g. use a client.connected flag and wait before every publish until true
    # > http://www.steves-internet-guide.com/client-connections-python-mqtt/
    client.subscribe("measurements")


def on_subscribe(client, userdata, message_id, granted_qos, properties=None):
    """The callback on SUBACK message from broker."""
    print(f"[SUBSCRIBED] message_id={message_id} qos={granted_qos}")
    # TODO ensure that we successfully subscribed > wait similar to connecting
    # http://www.steves-internet-guide.com/subscribing-topics-mqtt-client/


def on_message(client, userdata, message):
    """The callback on PUBLISH message from broker."""
    print(
        f"[RECEIVED] payload={message.payload} "
        f"topic={message.topic} "
        f"qos={message.qos} "
        f"retain={message.retain}"
    )


def on_publish(client, userdata, message_id):
    """The callback on PUBACK (resp. PUBCOMP for QoS=2?) message from broker.

    Messages sent with QoS=0 are acknowledged by the sending client instead.

    """
    pass


def on_disconnect(client, userdata, reason_code):
    """The callback on DISCONNECT message from broker."""
    print(f"[DISCONNECTED] reason_code={reason_code}")
    # TODO on abnormal disconnect > set flag, try to reconnect in main loop


client = mqtt.Client(client_id="", userdata=None, protocol=mqtt.MQTTv5)
client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_publish = on_publish

# enable TLS for secure connection
client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
# set username and password
client.username_pw_set(settings.MQTT_IDENTIFIER, settings.MQTT_PASSWORD)
# connect on port 8883 (the default for MQTT)
client.connect(settings.MQTT_URL, port=8883, keepalive=60)


client.loop_forever()
