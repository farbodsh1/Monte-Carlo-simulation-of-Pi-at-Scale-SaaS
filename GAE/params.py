import os

class Params:
    # AWS General Configs
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_REGION_NAME = os.environ.get("AWS_REGION_NAME")
    
    # AWS Lambda Configs
    AWS_LAMBDA_APIGATEWAY_HOSTNAME = os.environ.get("AWS_LAMBDA_APIGATEWAY_HOSTNAME") or "https://jv2xwrd10h.execute-api.us-west-1.amazonaws.com/test"
    AWS_LAMBDA_APIGATEWAY_ENDPOINT = os.environ.get("AWS_LAMBDA_APIGATEWAY_ENDPOINT") or "calculation"
    AWS_LAMBDA_APIGATEWAY_API_KEY = os.environ.get("AWS_LAMBDA_APIGATEWAY_API_KEY")
    AWS_LAMBDA_SET_MEMORY_MB = 512
    AWS_LAMBDA_GB_SEC_COST = 0.0000166667 # $
    
    # AWS EC2 Configs
    AWS_EC2_ENDPOINT = os.environ.get("AWS_EC2_ENDPOINT") or "calculation"
    AWS_EC2_AMI = "ami-05b6cba96a21eed8d"
    AWS_EC2_SG_NAME = "compute-pi-SG"
    AWS_EC2_TYPE = "t2.micro"
    AWS_EC2_KEYNAME = "mykeypair"
    AWS_EC2_HOUR_COST = 0.0116 # $
    AWS_EC2_USER_DATA = \
    """#!/bin/bash
    sudo service docker start
    sudo docker run --name compute-container -d -p 80:80 compute-img
    """

    # Flask Configs
    APP_PI_SECRET_KEY = os.environ.get("APP_PI_SECRET_KEY")
    APP_SESSION_LIFETIME_DAYS = os.environ.get("APP_SESSION_LIFETIME_DAYS") or 30
    APP_SHORT_WAIT = 10 # sec
    APP_DEV_DEBUG = False
    APP_DEV_HOST = "0.0.0.0"
    APP_DEV_PORT = 8080

    # Computation Configs
    MAX_PI_CALC_RETRIES = os.environ.get("MAX_PI_CALC_RETRIES") or 10
    ROUND_VALUES_DP = os.environ.get("ROUND_VALUES_DP") or 12
