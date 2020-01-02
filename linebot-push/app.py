import os

from linebot import LineBotApi
from linebot.models import ImageSendMessage, TextSendMessage

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))


def lambda_handler(event, context):
    print("Requested user id: %s" % event["user_id"])
    if "message" in event:
        message = event["message"]
        print("Requested message: %s" % message)
    else:
        message = None
    if "image" in event:
        image = event["image"]
        print("Requested image: %s" % image)
    else:
        image = None

    send_message(event["user_id"], message, image)
    return {"message": "OK"}


def send_message(id=None, message=None, image=None):
    messages = []

    if message is not None:
        messages.append(TextSendMessage(text=message))

    if image is not None:
        messages.append(
            ImageSendMessage(
                original_content_url=image["full"]["url"],
                preview_image_url=image["thumb"]["url"],
            )
        )

    if messages:
        print("Send message with data: %s" % messages)
        line_bot_api.push_message(id, messages=messages)
