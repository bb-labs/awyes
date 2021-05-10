import os
import sys
import json
import boto3
import docker
from collections import defaultdict


class Deployment():
    ecr_client = boto3.client('ecr')
    iam_client = boto3.client('iam')
    event_client = boto3.client('events')
    lambda_client = boto3.client('lambda')

    docker_client = docker.APIClient(base_url='unix://var/run/docker.sock')

    def __init__(self, config_path, source_path, root_path='.'):
        self.root_path = root_path
        self.config_path = config_path
        self.source_path = source_path
        self.shared = defaultdict(dict)

        with open(f"{self.root}/config.json") as config:
            self.config = json.load(config)

        for root, dirs, files in os.walk(self.root):
            self.images = list(
                filter(lambda file: 'Dockerfile' in file, files)
            )

    from .role import deploy_roles
    from .event import deploy_events
    from .layer import deploy_layers
    from .image import deploy_images
    from .function import deploy_lambdas

    def deploy(self):
        self.deploy_images()
        # self.deploy_roles()
        # self.deploy_events()
        # self.deploy_layers()
        # self.deploy_lambdas()


# if __name__ == '__main__':
#     script, config_path = sys.argv

#     Deployment(config_path=config_path).deploy()
