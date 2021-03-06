import json
import os
import re

import boto3

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))


def lambda_handler(event, context):
    signature = event["headers"]["X-Line-Signature"]
    body = event["body"]
    print("Message received with boty: %s" % body)

    response_ok = {
        "statusCode": 200,
        "headers": {},
        "body": "OK",
    }
    response_ng = {
        "statusCode": 403,
        "headers": {},
        "body": "Forbidden",
    }

    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        return response_ng
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        return response_ng

    return response_ok


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


@handler.add(MessageEvent, message=TextMessage)
def on_message(line_event):

    print("Received line event: %s" % line_event)
    message = line_event.message.text

    reply_verbose = {"reply": False, "body": ""}
    reply_body = ""
    reply_error = "ごめん、なんかエラーだって…… もう一回やってみて！"

    if re.search(r".* /v$", message):
        reply_verbose["reply"] = True
        message = re.sub(r" /v$", "", message)

    LAMBDA_AIRCONTROL = "SMARTHOME-AirControl"
    LAMBDA_QOAIR = "SMARTHOME-QoAir"
    LAMBDA_HUMIDIFIER = "SMARTHOME-Humidifier"
    LAMBDA_ACCOUNTING = "SMARTHOME-Accounting"
    LAMBDA_LINE_PUSH = "SMARTHOME-LineBot-Push"

    ptn = {
        "ACCOUNTING_LOGGING": re.compile(r".+[,、 　][0-9]+ *円*$"),
        "HUMIDIFIER_TURN_ON": re.compile(r"(加湿器).*(つ|付)けて"),
        "HUMIDIFIER_TURN_OFF": re.compile(r"(加湿器).*(け|消)して"),
        "AIRCONTROL_TURN_ON_WITH_MODE": re.compile(r"((暖|冷)房|クーラ(ー|)).*(つ|付)けて"),
        "AIRCONTROL_TURN_ON": re.compile(r"(つ|付)けて"),
        "AIRCONTROL_TURN_OFF": re.compile(r"(け|消)して"),
        "AIRCONTROL_CHANGE_TEMPERATURE": re.compile(r"([1-2][0-9]\s*度にして)"),
        "AIRCONTROL_CHANGE_MODE": re.compile(r"((暖|冷)房|クーラ(ー|))にして"),
        "AIRCONTROL_GET_CURRENT_SETTING": re.compile(r"(いま|今).*設定"),
        "DEBUG_AIRCONTROL_GET_APPLIANCE_LIST": re.compile(r"/debug ac list"),
        "QOAIR_GET_CURRENT_QOA": re.compile(r"(いま|今).*(空気|状態|どう|どんな(感じ|かんじ))"),
        "QOAIR_GET_GRAPH": re.compile(r"グラフ|推移|経緯"),
    }

    res = {"None": "None"}

    if ptn["ACCOUNTING_LOGGING"].fullmatch(message):
        match = re.search(r"(?P<item>.+)[,、 　](?P<price>[0-9]+) *円*$", message)
        req = {
            "operation": "append",
            "user_id": line_event.source.user_id,
            "item": match.group("item"),
            "price": match.group("price"),
        }
        line = {
            "user_id": req["user_id"],
            "message": "%s、%s 円、記録するね。" % (req["item"], req["price"])
        }
        linepush = post_lambda(LAMBDA_LINE_PUSH, line, True)
        print("Replied: %s" % linepush)
        res = post_lambda(LAMBDA_ACCOUNTING, req)

        if "updates" in res:
            reply_body = "記録したよ！"
        else:
            reply_body = reply_error

    elif ptn["HUMIDIFIER_TURN_ON"].search(message):
        req = {
            "operation": "post",
            "switch": "ON",
        }
        res = post_lambda(LAMBDA_HUMIDIFIER, req)

        if "switch" in res:
            reply_body = "加湿器つけたよ！"
        else:
            reply_body = reply_error

    elif ptn["HUMIDIFIER_TURN_OFF"].search(message):
        req = {
            "operation": "post",
            "switch": "OFF",
        }
        res = post_lambda(LAMBDA_HUMIDIFIER, req)

        if "switch" in res:
            reply_body = "加湿器消したよ！"
        else:
            reply_body = reply_error

    elif ptn["AIRCONTROL_TURN_ON_WITH_MODE"].search(message):
        if re.search(r"冷房|クーラ(ー|)", message):
            mode = "cooling"
        else:
            mode = "heating"

        req = {
            "operation": "post",
            "switch": "ON",
            "mode": mode,
        }
        res = post_lambda(LAMBDA_AIRCONTROL, req)

        if "mode_ja" in res:
            reply_body = "%sつけたよ！ %s 度になってる！" % (res["mode_ja"], res["temp"])
        else:
            reply_body = reply_error

    elif ptn["AIRCONTROL_TURN_ON"].search(message):
        req = {
            "operation": "post",
            "switch": "ON",
        }
        res = post_lambda(LAMBDA_AIRCONTROL, req)

        if "mode_ja" in res:
            reply_body = "%sつけたよ！ %s 度になってる！" % (res["mode_ja"], res["temp"])
        else:
            reply_body = reply_error

    elif ptn["AIRCONTROL_TURN_OFF"].search(message):
        req = {
            "operation": "post",
            "switch": "OFF",
        }
        res = post_lambda(LAMBDA_AIRCONTROL, req)

        if "mode_ja" in res:
            reply_body = "%s消したよ！" % (res["mode_ja"])
        else:
            reply_body = reply_error

    elif ptn["AIRCONTROL_CHANGE_TEMPERATURE"].search(message):
        match = re.search(r"[1-2][0-9]+", message)
        req = {
            "operation": "post",
            "temperature": match.group(),
        }
        res = post_lambda(LAMBDA_AIRCONTROL, req)

        if "mode_ja" in res:
            reply_body = "%s 度にしたよ！ %sね！" % (res["temp"], res["mode_ja"])
        else:
            reply_body = reply_error

    elif ptn["AIRCONTROL_CHANGE_MODE"].search(message):
        if re.search(r"冷房|クーラ(ー|)", message):
            mode = "cooling"
        else:
            mode = "heating"

        req = {
            "operation": "post",
            "mode": mode,
        }
        res = post_lambda(LAMBDA_AIRCONTROL, req)

        if "mode_ja" in res:
            reply_body = "%sにしたよ！ %s 度ね！" % (res["mode_ja"], res["temp"])
        else:
            reply_body = reply_error

    elif ptn["AIRCONTROL_GET_CURRENT_SETTING"].search(message):
        req = {
            "operation": "get",
            "get": "current_setting",
        }
        res = post_lambda(LAMBDA_AIRCONTROL, req)

        if "mode_ja" in res:
            reply_body = "今は%sで、電源は%s。設定は%s度！" % (
                res["mode_ja"],
                res["button_ja"],
                res["temp"],
            )
        else:
            reply_body = reply_error

    elif ptn["DEBUG_AIRCONTROL_GET_APPLIANCE_LIST"].search(message):
        req = {
            "operation": "get",
            "get": "debug_appliance_list",
        }
        res = post_lambda(LAMBDA_AIRCONTROL, req)
        if len(res) > 0:
            for cursor in res:
                reply_body += "%s (%s): %s\n" % (
                    cursor["name"],
                    cursor["nickname"],
                    cursor["id"],
                )

    elif ptn["QOAIR_GET_CURRENT_QOA"].search(message):
        req = {
            "operation": "get_current_qoa",
        }
        res = post_lambda(LAMBDA_QOAIR, req)

        if "temperature" in res:
            reply_body = "室温は %s 度で湿度は %s %%、気圧は %s hPa。\n二酸化炭素濃度は %s ppm だって！" % (
                res["temperature"],
                res["humidity"],
                res["airpressure"],
                res["co2concentration"],
            )
            reply_body += qoair_comment(res)
        else:
            reply_body = reply_error

    elif ptn["QOAIR_GET_GRAPH"].search(message):
        req = {
            "operation": "get_graph",
            "send_to_line_user": line_event.source.user_id,
            "send_to_line_message": "できたよ！",
        }

        ptns = [
            {
                "type": "all",
                "regex": r"全部"
            },
            {
                "type": "temperature",
                "regex": r"温度"
            },
            {
                "type": "humidity",
                "regex": r"湿度"
            },
            {
                "type": "airpressure",
                "regex": r"気圧"
            },
            {
                "type": "co2concentration",
                "regex": r"二酸化炭素|濃度"
            }
        ]

        graph_type = "all"
        for ptn in ptns:
            if re.search(ptn["regex"], message):
                graph_type = ptn["type"]

        req["graph_type"] = graph_type

        req["graph_duration"] = "6h"
        match = re.search(r"(?P<duration>[0-9]+) *(?P<unit>時間|分)", message)
        if match:
            unit = {
                "時間": "h",
                "分": "m",
            }
            req["graph_duration"] = match.group("duration")
            req["graph_duration"] += unit[match.group("unit")]

        print("Request generate and send graph: %s" % req)
        res = post_lambda(LAMBDA_QOAIR, req)

        if "message" in res:
            reply_body = "ちょっとまってね。"
        else:
            reply_body = reply_error

    reply_verbose["body"] += json.dumps(res, ensure_ascii=False) + "\n"

    if reply_verbose["reply"]:
        reply_body = reply_verbose["body"] + reply_body

    line_bot_api.reply_message(line_event.reply_token, TextSendMessage(text=reply_body))


def qoair_comment(data):
    comment = ""

    if float(data["temperature"]) < 20:
        comment += "寒いね、暖房つけない？ "
    elif float(data["temperature"]) > 28:
        comment += "暑いね…… 冷房つけない？ "

    if float(data["humidity"]) < 40:
        comment += "乾燥してるね、気を付けて！ "
    elif float(data["humidity"]) > 60:
        comment += "ジメジメ気味だよ、気を付けて！ "

    if float(data["co2concentration"]) > 1000:
        comment += "眠くなる二酸化炭素濃度だよ、換気しよう！"

    if comment != "":
        comment = "\n" + comment

    return comment
