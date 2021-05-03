import sys
import json
import boto3
from collections import defaultdict


class Deployment():
    iam_client = boto3.client('iam')
    event_client = boto3.client('events')
    lambda_client = boto3.client('lambda')

    def __init__(config_path):
        with open(config_path) as config:
            self.config = json.load(config)

        self.shared = defaultdict(dict)

    from role import deploy_role
    from event import deploy_event
    from layer import deploy_layer
    from function import deploy_lambda
