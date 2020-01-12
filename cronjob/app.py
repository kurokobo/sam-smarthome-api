import json
import os

import boto3


def post_lambda(name, dict, nohead=False):

    print("Invoke Lambda : %s" % name)
    print("Invoke Lambda with data : %s" % dict)
    if nohead:
        request = dict
    else:
        request = {
            "headers": {
                "X-Smarthome-Authorization": os.getenv("SMARTHOME_ACCESS_TOKEN")
            },
            "body": json.dumps(dict),
        }

    response = (
        boto3.client("lambda")
        .invoke(
            FunctionName=name,
            InvocationType="RequestResponse",
            Payload=json.dumps(request),
        )["Payload"]
        .read()
        .decode("utf-8")
    )

    if not nohead:
        response = json.loads(response)["body"]

    response = json.loads(response)

    print("Response body is : %s" % response)
    return response


def lambda_handler(event, context):

    print("Cron invoked with event: %s" % event)
    LAMBDA_AIRCONTROL = "SMARTHOME-AirControl"
    LAMBDA_QOAIR = "SMARTHOME-QoAir"
    LAMBDA_LINE_PUSH = "SMARTHOME-LineBot-Push"
    LAMBDA_HUMIDIFIER = "SMARTHOME-Humidifier"

    req = {
        "operation": "get_current_qoa",
    }
    qoa = post_lambda(LAMBDA_QOAIR, req)
    print("Current QoA is: %s" % qoa)

    if float(qoa["temperature"]) < 15.0:
        req = {
            "operation": "post",
            "mode": "heating",
            "temperature": 22,
        }
        res = post_lambda(LAMBDA_AIRCONTROL, req)
        if "mode_ja" in res:
            line = {
                "user_id": os.getenv("LINE_MASTER_USER_ID"),
                "message": "寒かったから暖房をつけたよ、22 度！",
            }
            print("Push line with data: %s" % line)
            res = post_lambda(LAMBDA_LINE_PUSH, line, True)

    elif float(qoa["temperature"]) > 29.0:
        req = {
            "operation": "post",
            "mode": "cooling",
            "temperature": 27,
        }
        res = post_lambda(LAMBDA_AIRCONTROL, req)
        if "mode_ja" in res:
            line = {
                "user_id": os.getenv("LINE_MASTER_USER_ID"),
                "message": "暑かった冷房をつけたよ、27 度！",
            }
            print("Push line with data: %s" % line)
            res = post_lambda(LAMBDA_LINE_PUSH, line, True)

    if float(qoa["humidity"]) < 40.0:
        req = {
            "operation": "post",
            "switch": "ON",
        }
        res = post_lambda(LAMBDA_HUMIDIFIER, req)
        if "switch" in res:
            line = {
                "user_id": os.getenv("LINE_MASTER_USER_ID"),
                "message": "乾燥してたから加湿器をつけたよ！",
            }
            print("Push line with data: %s" % line)
            res = post_lambda(LAMBDA_LINE_PUSH, line, True)

    response = {
        "statusCode": 200,
        "headers": {},
        "body": json.dumps(res),
    }
    print("Response with: %s" % response)
    return response
