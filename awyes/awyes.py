import os
import re
import copy
import boto3
import docker
import yaml
import json
import base64
import argparse

from textwrap import indent
from os.path import normpath

from .utils import rgetattr, rsetattr, rhasattr, Colors


class Deployment:
    def __init__(self, **kwargs):
        self.path = kwargs.get("path")
        self.workflow = kwargs.get("workflow")
        self.verbose = kwargs.get("verbose", True)
        self.dry_run = kwargs.get("dry_run", False)
        self.config = yaml.safe_load(kwargs.get("config"))

        if not self.config:
            with open(normpath(self.path)) as config:
                self.config = yaml.safe_load(config)

        self.ir = copy.deepcopy(self.config)

        self.clients = {
            "os": os,
            "re": re,
            "base64": base64,
            "s3": boto3.client("s3"),
            "ecr": boto3.client("ecr"),
            "sts": boto3.client("sts"),
            "rds": boto3.client("rds"),
            "iam": boto3.client("iam"),
            "events": boto3.client("events"),
            "lambda": boto3.client("lambda"),
            "docker": docker.client.from_env(),
        }

    def get_fully_qualified_node_names(self):
        return [f"{resource_name}.{action_name}"
                for resource_name, actions in self.config.items()
                for action_name in actions.keys()]

    def visit_parents(self, node_name, seen=set(), sorted_nodes=[]):
        if node_name in seen:
            return

        node = rgetattr(self.config, node_name)

        if not rhasattr(node, "workflow"):
            raise Exception(
                f"{node_name} is missing workflow tags.")

        node.setdefault("name", node_name)
        node.setdefault("args", {})
        node.setdefault("depends_on", [])

        seen.add(node_name)

        for parent_node_name in node.get("depends_on"):
            self.visit_parents(parent_node_name. seen, sorted_nodes)

        sorted_nodes.append(node)

        return sorted_nodes

    def get_topologically_sorted_nodes(self):
        sorted_nodes = []

        for node_name in self.get_fully_qualified_node_names():
            self.visit_parents(node_name, sorted_nodes=sorted_nodes)

        return sorted_nodes

    def lookup(self, args):
        if isinstance(args, dict):
            for key, value in args.items():
                args[key] = self.lookup(value)

            return args

        if isinstance(args, list):
            return list(map(lambda value: self.lookup(value), args))

        if isinstance(args, bytes):
            return args.decode()

        if isinstance(args, str):
            match = re.search("\$\((?P<reference>.*)\)", args)

            if not match:
                return args

            value = self.lookup(
                rgetattr(self.ir, match.group("reference")))

            return re.sub(re.escape(match.group()), value, args) \
                if isinstance(value, str) else value

        return args

    def execute(self, node):
        node_name = rgetattr(node, "name")
        node_args = rgetattr(node, "args")
        node_client = rgetattr(self.clients, rgetattr(node, "client"))
        resource_name, action_name = node_name.split(".")

        if self.verbose:
            print(f"{Colors.OKCYAN}{node_name}{Colors.ENDC}")

        try:
            action = rgetattr(node_client, action_name)
            value = action(**self.lookup(node_args))
            if self.verbose:
                print(indent(json.dumps(value, indent=2,
                                        default=str), '+ ', lambda _: True))

            rsetattr(
                context=self.ir,
                accessor=f"{resource_name}.{action_name}",
                value=value,
            )
        except Exception as e:
            if self.verbose:
                print(indent(json.dumps(e, indent=2, default=str),
                             '- ', lambda _: True))

    def summarize(self, nodes):
        print(f"{Colors.UNDERLINE}Executing nodes for: \
               {self.workflow if self.workflow else self.action}{Colors.ENDC}")

        for node in nodes:
            print(f"{Colors.BOLD}{rgetattr(node, 'name')}{Colors.ENDC}")

        print('------------------------------------------')

    def deploy(self):
        workflow_nodes = []
        for node in self.get_topologically_sorted_nodes():
            if self.workflow in rgetattr(node, "workflow"):
                workflow_nodes.append(node)

        if self.verbose:
            self.summarize(workflow_nodes)

        if self.dry_run:
            return

        for node in workflow_nodes:
            self.execute(node)

    def one_off(self, node_name):
        dependencies = self.visit_parents(node_name)

        if self.verbose:
            self.summarize(dependencies)

        if self.dry_run:
            return

        for node in dependencies:
            self.execute(node)


def main():
    parser = argparse.ArgumentParser(description='Create an awyes deployment')

    parser.add_argument('--dry_run', action=argparse.BooleanOptionalAction)
    parser.add_argument('--verbose', action=argparse.BooleanOptionalAction)
    parser.add_argument('--workflow', type=str, required=False,
                        help='The awyes workflow type')
    parser.add_argument('--path', type=str, required=False,
                        default="awyes.yml", help='Path to awyes config')
    parser.add_argument('--config', type=str, required=False,
                        help='Raw config to use in place of path')
    parser.add_argument('--action', type=str, required=False,
                        help="A specific action to run")

    args = parser.parse_args()
    deployment = Deployment(**vars(args))

    if args.action:
        deployment.one_off(args.action)
    elif args.workflow:
        deployment.deploy()
    else:
        raise "Please pass either a workflow tag or an action"


if __name__ == '__main__':
    main()
