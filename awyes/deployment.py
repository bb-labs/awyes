import boto3
import docker

from sys import argv
from pprint import pprint
from re import sub, search
from yaml import safe_load
from base64 import b64decode
from operator import itemgetter
from utils import access, insert
from os.path import normpath, join


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

        # Load the config and docker images
        with open(normpath(join(self.root, 'awyes.yml'))) as config:
            self.config = safe_load(config)
            self.config.update(Deployment.clients)

        # Login to docker
        Deployment.clients['docker'].login(
            username="AWS",
            password=self.ecr_password,
            registry=f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com"
        )

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

    def topological_traverse(self, node_name, seen=set(), result=[]):
        if node_name in seen:
            return result

        seen.add(node_name)

        for other_node_name in access(self.config, node_name).get('depends_on', []):
            self.topological_traverse(other_node_name, seen, result)

        # Associate the action name with the node_name
        action = access(self.config, node_name)
        action_name, resource_name = node_name.split('.')
        action['action'] = action_name
        action['resource'] = resource_name

        result.append(action)

        return result

    def topological_ordering(self):
        seen = set()
        sorted_nodes = []

        # Loop over each resource
        for resource_name, actions in self.config.items():
            # Loop over each action
            for action_name, metadata in actions.items():
                metadata.setdefault('depends_on', [])

                # Mutates sorted_nodes
                self.topological_traverse(
                    node_name=f"{resource_name}.{action_name}",
                    seen=seen,
                    result=sorted_nodes
                )

        return sorted_nodes

    def shared_lookup(self, args):
        if isinstance(args, dict):
            for key, value in args.items():
                args[key] = self.shared_lookup(value)

            return args

        if isinstance(args, list):
            return list(map(lambda value: self.shared_lookup(value), args))

        if isinstance(args, str):
            match = search('\((?P<reference>.*)\)', args)

            if not match:
                return args

            return access(self.config, match.group('reference'))

        return args

    def deploy(self):
        # Unpack action metadata
        unpack = itemgetter('args', 'client', 'action', 'resource')

        for step in self.topological_ordering():
            args, client_name, action_name, resource_name = unpack(step)

            client = access(self.config, client_name)
            action = getattr(client, action_name)

            insert(
                context=self.config,
                accessor=f"{resource_name}.{action_name}",
                value=action(**args)
            )


if __name__ == '__main__':
    _, root = argv

    Deployment(root=root).deploy()
