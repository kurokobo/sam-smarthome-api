import datetime
import json

import boto3

import graph
import influxdb
import s3


def lambda_handler(event, context):
    print("Requested graph: %s" % event["type"])
    print("Requested duration: %s" % event["duration"])

    if "send_to_line_user" in event and event["send_to_line_user"] != "":
        send_line = True
        print("Send graph image to line user: %s" % event["send_to_line_user"])

        if "send_to_line_message" in event and event["send_to_line_message"] != "":
            send_line_message = event["send_to_line_message"]
            print("Send graph image with message: %s" % event["send_to_line_message"])

    else:
        print("Generate graph without any additional action")
        send_line = False
        send_line_message = None

    df = influxdb.get_dataframe(event["type"], event["duration"])
    images = graph.generate_graph(df)

    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename_full = "g-%s-%s.jpg" % (event["type"][0:3], now)
    filename_thumb = "g-%s-%s_thumb.jpg" % (event["type"][0:3], now)

    uploads = [
        {"type": "full", "filename": filename_full, "image": images["full"]},
        {"type": "thumb", "filename": filename_thumb, "image": images["thumb"]},
    ]

    images = s3.upload_s3(uploads)

    print("Image has uploaded as: %s" % images)

    if send_line:
        request = {
            "user_id": event["send_to_line_user"],
            "image": images,
        }
        if send_line_message is not None:
            request["message"] = event["send_to_line_message"]

        print("Send graph with data: %s" % request)

        boto3.client("lambda").invoke(
            FunctionName="SMARTHOME-LineBot-Push",
            InvocationType="Event",
            Payload=json.dumps(request),
        )["Payload"].read().decode("utf-8")
