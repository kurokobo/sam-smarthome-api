import json
import os
import secrets
from datetime import datetime, timedelta, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SPREADSHEET_RANGE = os.getenv("SPREADSHEET_RANGE")
SERVICE_ACCOUNT_FILE = "credentials.json"
JST = timezone(timedelta(hours=+9), "JST")


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

    if input["operation"] == "append":
        response_dict = append_spreadsheet(
            input["user_id"], input["item"], input["price"]
        )

    response = {
        "statusCode": 200,
        "headers": {},
        "body": json.dumps(response_dict),
    }
    return response


def append_spreadsheet(user_id, item, price):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=credentials)

    sheet = service.spreadsheets()
    values = {}
    values["range"] = SPREADSHEET_RANGE
    values["majorDimension"] = "ROWS"
    values["values"] = [
        [datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S"), user_id, item, price]
    ]
    valueInputOption = "USER_ENTERED"
    response = (
        sheet.values()
        .append(
            spreadsheetId=SPREADSHEET_ID,
            range=SPREADSHEET_RANGE,
            valueInputOption=valueInputOption,
            body=values,
        )
        .execute()
    )

    print("Current values: %s" % response)
    return response
