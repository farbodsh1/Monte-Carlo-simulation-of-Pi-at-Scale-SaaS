import json
import random
import time
import uuid
import requests

import boto3

from params import Params


ec2_resource = boto3.resource('ec2', aws_access_key_id=Params.AWS_ACCESS_KEY_ID, aws_secret_access_key=Params.AWS_SECRET_ACCESS_KEY, region_name=Params.AWS_REGION_NAME)
ec2_client = boto3.client('ec2', aws_access_key_id=Params.AWS_ACCESS_KEY_ID, aws_secret_access_key=Params.AWS_SECRET_ACCESS_KEY, region_name=Params.AWS_REGION_NAME)

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


# parallel call a given API
def call_api(config):
    try:
        response = config['session'].get(url=config['url'])
        if response.status_code != 200:
            print(f"API returned response {response.status_code} for {config['url']}")
            print(response.json())
            return "error"
        else:
            response = response.json() # to dict
            if response["status"]=="ok":
                return response["result"], response["duration"]
                # returns a list as partial result and duration of a single call
            else:
                return "error"
    except Exception as err:
        print(f"unknown error {err}")
        return "error"


def generate_aws_lambda_configs(subshots, report_rate, resources_count):
    session = requests.Session()
    session.headers.update({'x-api-key':Params.AWS_LAMBDA_APIGATEWAY_API_KEY})
    lambda_configs = [{
        "url":\
            f"{Params.AWS_LAMBDA_APIGATEWAY_HOSTNAME}/"
            f"{Params.AWS_LAMBDA_APIGATEWAY_ENDPOINT}"
            f"?subshots={subshots}"
            f"&report_rate={report_rate}"
            f"&resource_id={str(uuid.uuid4())}",
        "session":session
    } for _ in range(resources_count)]
    return lambda_configs


def generate_aws_ec2_configs(subshots, report_rate, resources_count, ec2_public_ips):
    session = requests.Session()
    ec2_configs = [{
        "url":\
            f"http://{ec2_public_ip}/"
            f"{Params.AWS_EC2_ENDPOINT}"
            f"?subshots={subshots}"
            f"&report_rate={report_rate}"
            f"&resource_id={str(uuid.uuid4())}",
        "session":session
    } for ec2_public_ip in ec2_public_ips[:resources_count]]
    return ec2_configs


def aws_create_ec2s(n_instances_to_start):
    # create a new EC2 instance
    instances = ec2_resource.create_instances(
        MinCount=n_instances_to_start,
        MaxCount=n_instances_to_start,
        ImageId=Params.AWS_EC2_AMI,
        InstanceType=Params.AWS_EC2_TYPE,
        SecurityGroups=[Params.AWS_EC2_SG_NAME],
        KeyName=Params.AWS_EC2_KEYNAME,
        UserData=Params.AWS_EC2_USER_DATA,
     )
    [instance.wait_until_running() for instance in instances]
    return instances


def aws_get_running_ips():
    # get ids and ips of running instances
    running_ips = {}
    for group in ec2_client.describe_instances()["Reservations"]:
        for instance in group["Instances"]:
            if instance.get("State", {}).get("Name", "") == "running":
                running_ips.update({instance["InstanceId"]:instance["PublicIpAddress"]})
    return running_ips


def aws_terminate_instances():
    # terminate all running instances
    running_ids = list(aws_get_running_ips().keys())
    if running_ids:
        ec2_client.terminate_instances(InstanceIds=running_ids)


def estimate_compute_cost(service, duration_sec):
    if service=="lambda":
        cost = duration_sec * Params.AWS_LAMBDA_SET_MEMORY_MB / 1024 * Params.AWS_LAMBDA_GB_SEC_COST
    elif service=="ec2":
        cost = duration_sec / 3600 * Params.AWS_EC2_HOUR_COST
    return cost
