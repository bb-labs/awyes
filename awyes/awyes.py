import os
import re
import copy
import boto3
import docker
import yaml
import json
import types
import base64
import builtins
import argparse

from textwrap import indent
from os.path import normpath

from .utils import rgetattr, rsetattr, rhasattr, Colors


class Deployment:
    def __init__(self, **kwargs):
        self.path = kwargs.get("path")
        self.verbose = kwargs.get("verbose")
        self.preview = kwargs.get("preview")
        self.config = yaml.safe_load(kwargs.get("config"))

        if not self.config:
            with open(normpath(self.path)) as config:
                self.config = yaml.safe_load(config)

        self.ir = copy.deepcopy(self.config)

        self.clients = {
            "os": os,
            "re": re,
            "base64": base64,
            "builtins": builtins,
            "docker": docker.client.from_env(),
            "s3": boto3.client("s3"),
            "ecr": boto3.client("ecr"),
            "sts": boto3.client("sts"),
            "rds": boto3.client("rds"),
            "iam": boto3.client("iam"),
            "events": boto3.client("events"),
            "lambda": boto3.client("lambda"),
            "apigateway": boto3.client('apigateway'),
            "organizations": boto3.client("organizations"),
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
            self.visit_parents(parent_node_name, seen, sorted_nodes)

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
            args = self.lookup(node_args)
            action = rgetattr(node_client, action_name)

            if isinstance(args, list):
                value = action(*args)
            elif isinstance(args, dict):
                value = action(**args)

            if isinstance(value, types.GeneratorType):
                value = list(value)  # auto unpack generators

            if self.verbose:
                self.print_status(value, Colors.OKGREEN)

            rsetattr(
                context=self.ir,
                accessor=f"{resource_name}.{action_name}",
                value=value)

        except Exception as e:
            self.print_status(e, Colors.FAIL)

    def summarize(self, nodes, plan):
        print(f"{Colors.UNDERLINE}Executing nodes for: \
              {plan}{Colors.ENDC}")

        for node in nodes:
            print(f"{Colors.BOLD}{rgetattr(node, 'name')}{Colors.ENDC}")

        print()

    def print_status(self, value, status):
        indicator = "+" if status == Colors.OKGREEN else "-"
        print(indent(json.dumps(value, indent=2,
                                default=str),
                     f"{status}{indicator} {Colors.ENDC}",
                     lambda _: True))

    def deploy(self, workflow):
        workflow_nodes = []
        for node in self.get_topologically_sorted_nodes():
            if workflow in rgetattr(node, "workflow"):
                workflow_nodes.append(node)

        if self.verbose:
            self.summarize(workflow_nodes, workflow)

        if self.preview:
            return

        for node in workflow_nodes:
            self.execute(node)

    def one_off(self, node_name, include_deps):
        dependencies = self.visit_parents(node_name)

        if not include_deps:
            dependencies = [dependencies.pop()]

        if self.verbose:
            self.summarize(dependencies, node_name)

        if self.preview:
            return

        for node in dependencies:
            self.execute(node)


def main():
    parser = argparse.ArgumentParser(description='Create an awyes deployment')

    parser.add_argument(
        '--preview', action=argparse.BooleanOptionalAction, default=False,
        help="Whether or not to execute the plan")
    parser.add_argument(
        '--verbose', action=argparse.BooleanOptionalAction, default=True,
        help="Enable logging")
    parser.add_argument(
        '--include-deps', action=argparse.BooleanOptionalAction, default=False,
        help="When specifying an action, whether to include dependent actions")

    parser.add_argument('--workflow', type=str, required=False, default="",
                        help='The awyes workflow type')
    parser.add_argument('--path', type=str, required=False,
                        default="awyes.yml", help='Path to awyes config')
    parser.add_argument('--config', type=str, required=False, default="",
                        help='Raw config to use in place of path')
    parser.add_argument('--action', type=str, required=False, default="",
                        help="A specific action to run")

    args = parser.parse_args()
    deployment = Deployment(**vars(args))

    if args.action:
        deployment.one_off(args.action, args.include_deps)
    elif args.workflow:
        deployment.deploy(args.workflow)
    else:
        raise "Please pass either a workflow tag or an action"


if __name__ == '__main__':
    main()
