import json
import os
import secrets
import ssl
from time import sleep

import paho.mqtt.client as mqtt

endpoint = os.getenv("IOT_CORE_ENDPOINT")
port = 8883
topic = "tuya/%s/%s/%s/command" % (
    os.getenv("TUYA_DEVICE_ID"),
    os.getenv("TUYA_LOCAL_KEY"),
    os.getenv("TUYA_IP_ADDRESS"),
)
rootca = "cert/rootca.pem"
cert = "cert/certificate.pem.crt"
key = "cert/private.pem.key"

flag_published = False


def is_authorized(event):
    if "X-Smarthome-Authorization" in event["headers"] and secrets.compare_digest(
        event["headers"]["X-Smarthome-Authorization"],
        os.getenv("SMARTHOME_ACCESS_TOKEN"),
    ):
        print("Authorized access")
        return True
    print("Unuthorized access")
    return False


def lambda_handler(event, context):
    if not is_authorized(event):
        return {
            "statusCode": 403,
            "body": {"message": "Forbidden"},
        }

    input = json.loads(event["body"])
    print("Requested operation: %s" % input["operation"])
    print("Requested status: %s" % input["switch"])

    if input["switch"] == "ON":
        response_dict = humidifier_switch(True)

    elif input["switch"] == "OFF":
        response_dict = humidifier_switch(False)

    response = {
        "statusCode": 200,
        "headers": {},
        "body": json.dumps(response_dict),
    }
    return response


def humidifier_switch(status):

    global flag_published
    flag_published = False
    client = mqtt.Client()

    def on_connect_on(client, userdata, flag, rc):
        print("Connected with code: %s" % rc)
        print("Publish to topic: %s" % topic)
        client.publish(topic, "ON")

    def on_connect_off(client, userdata, flag, rc):
        print("Connected with code: %s" % rc)
        print("Publish to topic: %s" % topic)
        client.publish(topic, "OFF")

    def on_disconnect(client, userdata, rc):
        print("Disconnected with code: %s" % rc)

    def on_publish(client, userdata, rc):
        print("Published: %s" % rc)
        global flag_published
        flag_published = True
        client.loop_stop()
        client.disconnect()

    def on_log(client, obj, level, string):
        print(string)

    if status:
        print("Set callback for ON")
        client.on_connect = on_connect_on
    else:
        print("Set callback for OFF")
        client.on_connect = on_connect_off

    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
    client.on_log = on_log

    try:
        client.tls_set(
            ca_certs=rootca,
            certfile=cert,
            keyfile=key,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2,
            ciphers=None,
        )
    except ValueError:
        pass

    print("Connect to: %s:%s" % (endpoint, port))
    client.connect(endpoint, port=port, keepalive=60)
    client.loop_start()

    for i in range(20):
        print("Status of publication: %s" % flag_published)

        if flag_published:
            break
        else:
            sleep(1)

    if flag_published:
        if status:
            response = {"switch": "ON"}
        else:
            response = {"switch": "OFF"}
    else:
        response = {"message": "failed"}

    print("Response with: %s" % response)
    return response
