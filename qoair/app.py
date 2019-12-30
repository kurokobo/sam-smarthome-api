import json
import os

import redis


def setup_redis():
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

    redisdb = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True
    )
    return redisdb


def lambda_handler(event, context):
    input = json.loads(event["body"])

    print("Requested operation: %s" % input["operation"])
    if input["operation"] == "get_current_qoa":
        response_dict = get_current_qoa()

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
