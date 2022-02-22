import json

def lambda_handler(event, context):

    print(event)

    index = event["index"]
    step = event["step"]
    count = event["count"]

    index += 1

    response = {
        "index": index,
        "step": step,
        "count": count,
        "continue": index < count
    }

    return response
