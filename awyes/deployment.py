import sys
import json
import boto3
from collections import defaultdict


class Deployment():
    iam_client = boto3.client('iam')
    event_client = boto3.client('events')
    lambda_client = boto3.client('lambda')

    def __init__(self, config_path):
        with open(config_path) as config:
            self.config = json.load(config)

        self.shared = defaultdict(dict)

    from .role import deploy_roles
    from .event import deploy_events
    from .layer import deploy_layers
    from .function import deploy_lambdas

    def deploy(self):
        self.deploy_roles()
        self.deploy_events()
        self.deploy_layers()
        self.deploy_lambdas()


if __name__ == '__main__':
    script, config_path = sys.argv

    Deployment(config_path=config_path).deploy()
