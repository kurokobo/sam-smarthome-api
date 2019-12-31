import json
import os
import secrets

import requests

REMO_BASEURL = "https://api.nature.global"
REMO_APPLIANCE_ID = os.getenv("REMO_APPLIANCE_ID")

mode_ja = {
    "warm": "暖房",
    "cool": "冷房",
    "dry": "ドライ",
}
button_ja = {
    "": "オン",
    "power-off": "オフ",
}


def is_authorized(event):
    if "X-SmartHome-Authorization" in event["headers"] and secrets.compare_digest(
        event["headers"]["X-SmartHome-Authorization"],
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
            "body": "Forbidden",
        }

    input = json.loads(event["body"])
    print("Requested operation: %s" % input["operation"])
    if input["operation"] == "post":
        response_dict = aircon_setting(input)
    elif input["operation"] == "get":
        response_dict = appliance(input)

    response = {
        "statusCode": 200,
        "headers": {},
        "body": json.dumps(response_dict),
    }
    return response


def request(method, path, dict={}):
    url = REMO_BASEURL + path
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Bearer " + os.getenv("REMO_ACCESS_TOKEN"),
    }

    if method.lower() == "get":
        print("Invoke GET with url : %s" % url)
        response = requests.get(url, headers=headers)
    else:
        print("Invoke POST with url : %s" % url)
        print("Invoke POST with data : %s" % json.dumps(dict))
        response = requests.post(url, dict, headers=headers)

    print("Response body is : %s" % response.json())
    return response.json()


def aircon_setting(input, id=REMO_APPLIANCE_ID):

    print("Update setting for : %s" % id)
    print("Requested settings : %s" % input)

    path = "/1/appliances/" + id + "/aircon_settings"
    config = {}

    if "switch" in input:
        if input["switch"].lower() == "off":
            config["button"] = "power-off"
        else:
            config["button"] = ""

    if "temperature" in input:
        config["temperature"] = input["temperature"]

    if "mode" in input:
        if input["mode"].lower() == "cooling":
            config["operation_mode"] = "cool"
        else:
            config["operation_mode"] = "warm"

    print("Update setting with : %s" % config)

    response = request("post", path, config)

    return localize(response)


def appliance(input, id=REMO_APPLIANCE_ID):

    path = "/1/appliances"
    response = request("get", path)

    print("Requested operation: %s" % input["get"])
    if input["get"] == "current_setting":
        for cursor in response:
            if cursor["id"] == id:
                target = cursor
                break

        setting = {
            "temp": target["settings"]["temp"],
            "mode": target["settings"]["mode"],
            "vol": target["settings"]["vol"],
            "dir": target["settings"]["dir"],
            "button": target["settings"]["button"],
            "updated_at": target["settings"]["updated_at"],
        }

        print("Current setting: %s" % setting)
        return localize(setting)

    elif input["get"] == "debug_appliance_list":
        appliance_list = []
        for cursor in response:
            appliance_list.append(
                {
                    "id": cursor["id"],
                    "name": cursor["device"]["name"],
                    "nickname": cursor["nickname"],
                }
            )

        print("Appliance list: %s" % appliance_list)
        return appliance_list


def localize(response):
    if "mode" in response:
        response["mode_ja"] = mode_ja[response["mode"]]
    if "button" in response:
        response["button_ja"] = button_ja[response["button"]]

    return response
