import json
import os
import secrets

import boto3

import redis


def setup_redis():
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

    redisdb = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True
    )
    return redisdb


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

    if input["operation"] == "get_current_qoa":
        response_dict = get_current_qoa()

    elif input["operation"] == "get_graph":
        if "graph_duration" in input:
            response_dict = generate_and_send_graph(
                input["send_to_line_user"],
                input["send_to_line_message"],
                input["graph_type"],
                input["graph_duration"],
            )
        else:
            response_dict = generate_and_send_graph(
                input["send_to_line_user"],
                input["send_to_line_message"],
                input["graph_type"],
            )

    response = {
        "statusCode": 200,
        "headers": {},
        "body": json.dumps(response_dict),
    }
    return response


def get_current_qoa():
    db = setup_redis()
    response = {
        "temperature": get_value_from_db(db, "sensor_temperature", "float"),
        "humidity": get_value_from_db(db, "sensor_humidity", "int"),
        "airpressure": get_value_from_db(db, "sensor_airpressure", "int"),
        "co2concentration": get_value_from_db(db, "sensor_co2concentration", "int"),
    }
    print("Current values: %s" % response)
    return response


def get_value_from_db(db, key, type):
    value = json.loads(db.get(key))["value"]
    if type == "int":
        return f"{float(value):.0f}"
    elif type == "float":
        return f"{float(value):.1f}"


def generate_and_send_graph(
    send_to_line_user, send_to_line_message, type="all", duration="6h"
):
    print("Requested graph: %s" % type)
    print("Requested duration: %s" % duration)
    print("Send graph to: %s" % send_to_line_user)
    print("Send graph with message: %s" % send_to_line_message)

    event = {
        "type": type,
        "duration": duration,
        "send_to_line_user": send_to_line_user,
        "send_to_line_message": send_to_line_message,
    }
    print("Throw process to Graph function with values: %s" % event)
    lambdaclient = boto3.client("lambda")
    lambdaclient.invoke(
        FunctionName="SMARTHOME-Graph",
        InvocationType="Event",
        Payload=json.dumps(event),
    )
    return {
        "message": "OK",
    }
