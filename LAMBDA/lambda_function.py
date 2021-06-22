import json
import random
import time

# part of AWS Lambda Function
def calculate_pi(config):
    subshots = int(config["subshots"])
    report_rate = int(config["report_rate"])
    resource_id = config["resource_id"]
    in_circle = 0
    res = []
    for shot_n in range(1, subshots+1):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        if (x**2 + y**2) < 1:
            in_circle += 1
        
        if shot_n%report_rate==0:
            res.append({
                "resource_id":resource_id,
                "in_circle":in_circle,
                "shots":report_rate,
            })
            in_circle = 0
    return res 


# part of AWS Lambda Function
def lambda_handler(event, context):
    try:
        start_time = time.perf_counter()
        operation = event['httpMethod']
        payload = event['queryStringParameters'] if operation == 'GET' else json.loads(event['body'])
        compute_result = calculate_pi(config=payload) # compute function
        finish_time = time.perf_counter()
        duration = finish_time - start_time
        result = {
            "status":"ok",
            "result":compute_result,
            "duration":duration,
        }
        body = json.dumps(result)
    except Exception as err:
        result = {
            "status":"failed",
            "result":None,
            "msg":str(err),
        }
        body = json.dumps(result)
    finally:
        response = {
            'statusCode': '200' if result["status"]=="ok" else '502',
            'body': body,
            'headers': {
                'Content-Type': 'application/json',
            },
        }
        return response
