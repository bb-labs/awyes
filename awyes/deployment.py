import sys
import boto3
import docker

from re import sub
from yaml import safe_load
from base64 import b64decode
from operator import itemgetter
from os.path import normpath, join
from collections import defaultdict

from utils import access


class Deployment():
    clients = {
        'ecr': boto3.client('ecr'),
        'sts': boto3.client('sts'),
        'iam': boto3.client('iam'),
        'events': boto3.client('events'),
        'lambda': boto3.client('lambda'),
        'session': boto3.session.Session(),
        'docker': docker.client.from_env(),
    }

    def __init__(self, root='.'):
        # Initialize paths and shared dictionary
        self.root = root
        self.shared = defaultdict(dict)

        # Load the config and docker images
        with open(normpath(join(self.root, 'awyes.yml'))) as config:
            self.config = safe_load(config)

        # Login to docker
        Deployment.clients['docker'].login(
            username="AWS",
            password=self.ecr_password,
            registry=f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com"
        )

        # Deployment order
        self.actions = self.order()

    @property
    def region(self):
        return Deployment.clients['session'].region_name

    @property
    def account_id(self):
        id_response = Deployment.clients['sts'].get_caller_identity()

        return id_response['Account']

    @property
    def ecr_password(self):
        token_response = Deployment.clients['ecr'].get_authorization_token()

        get_data = itemgetter('authorizationData')
        get_token = itemgetter('authorizationToken')

        token = get_token(get_data(token_response).pop())

        return sub("AWS:", "", b64decode(token).decode())

    def topological_traverse(self, node, seen=set(), result=[]):
        if node in seen:
            return result

        seen.add(node)

        for other_node in access(self.config, node).get('depends_on', []):
            self.topological_traverse(other_node, seen, result)

        result.insert(0, access(self.config, node))

        return result

    def order(self):
        seen = set()
        sorted_nodes = []

        # Loop over each client
        for resource, steps in self.config.items():
            # Loop over each step
            for action, metadata in steps.items():
                metadata.setdefault('output', False)
                metadata.setdefault('depends_on', [])

                # Mutates sorted_nodes
                self.topological_traverse(
                    node=f"{resource}.{action}",
                    seen=seen,
                    result=sorted_nodes
                )

        return sorted_nodes

    def deploy(self):
        # Unpack action metadata
        unpack = itemgetter('depends_on', 'output', 'args', 'client')

        pass


if __name__ == '__main__':
    _, root = sys.argv

    Deployment(root=root).deploy()
