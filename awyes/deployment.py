import json
import boto3
import docker

from re import sub
from base64 import b64decode
from operator import itemgetter
from os.path import normpath, join
from collections import defaultdict


class Deployment():
    session = boto3.session.Session()
    ecr_client = boto3.client('ecr')
    sts_client = boto3.client('sts')
    iam_client = boto3.client('iam')
    event_client = boto3.client('events')
    lambda_client = boto3.client('lambda')
    docker_client = docker.client.from_env()

    def __init__(self, config_path, source_path, root_path='.'):
        # Initialize paths and shared dictionary
        self.root_path = root_path
        self.config_path = config_path
        self.source_path = source_path
        self.shared = defaultdict(dict)

        # Load the config and docker images
        with open(normpath(join(self.root_path, self.config_path, 'config.json'))) as config:
            self.config = json.load(config)

        # Login to docker
        Deployment.docker_client.login(
            username="AWS",
            password=self.ecr_password,
            registry=f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com"
        )

    from .role import deploy_roles
    from .event import deploy_events
    from .layer import deploy_layers
    from .image import deploy_images
    from .function import deploy_lambdas

    @property
    def region(self):
        return Deployment.session.region_name

    @property
    def account_id(self):
        id_response = Deployment.sts_client.get_caller_identity()

        return itemgetter('Account')(id_response)

    @property
    def ecr_password(self):
        token_response = Deployment.ecr_client.get_authorization_token()

        get_data = itemgetter('authorizationData')
        get_token = itemgetter('authorizationToken')

        token = get_token(get_data(token_response).pop())

        return sub("AWS:", "", b64decode(token).decode())

    def deploy(self):
        self.deploy_images()
        # self.deploy_roles()
        # self.deploy_events()
        # self.deploy_layers()
        # self.deploy_lambdas()
