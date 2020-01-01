def lambda_handler(event, context):
    input = event
    print("Requested graph: %s" % input["type"])
    print("Requested duration: %s" % input["duration"])
