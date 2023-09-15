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
        if 'workflow' not in kwargs:
            raise "Please pass a workflow tag"

        self.path = kwargs.get("path")
        self.workflow = kwargs.get("workflow")
        self.preview = kwargs.get("preview", False)
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

    def get_topologically_sorted_nodes(self, seen=set(), sorted_nodes=[]):
        for node_name in self.get_fully_qualified_node_names():
            def visit_parents(node_name):
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
                    visit_parents(parent_node_name)

                sorted_nodes.append(node)

            visit_parents(node_name)

        return sorted_nodes

    def shared_lookup(self, args):
        if isinstance(args, dict):
            for key, value in args.items():
                args[key] = self.shared_lookup(value)

            return args

        if isinstance(args, list):
            return list(map(lambda value: self.shared_lookup(value), args))

        if isinstance(args, bytes):
            return args.decode()

        if isinstance(args, str):
            match = re.search("\$\((?P<reference>.*)\)", args)

            if not match:
                return args

            value = self.shared_lookup(
                rgetattr(self.ir, match.group("reference")))

            return re.sub(re.escape(match.group()), value, args) \
                if isinstance(value, str) else value

        return args

    def deploy(self):
        print(f"{Colors.UNDERLINE}Executing workflow: \
              {self.workflow}{Colors.ENDC}")

        workflow_nodes = []
        for node in self.get_topologically_sorted_nodes():
            node_name = rgetattr(node, "name")

            # Ensure this node is part of the workflow
            if self.workflow in rgetattr(node, "workflow"):
                print(
                    f"{Colors.BOLD}{node_name}{Colors.ENDC}")

                workflow_nodes.append(node)

        if self.preview:
            return

        for node in workflow_nodes:
            node_name = rgetattr(node, "name")

            # Print the node name
            print(f"{Colors.OKCYAN}{node_name}{Colors.ENDC}")

            # Resolve the client
            node_args = rgetattr(node, "args")
            node_client = rgetattr(self.clients, rgetattr(node, "client"))

            # Resolve any args, run the action, and save the result
            resource_name, action_name = node_name.split(".")
            try:
                action = rgetattr(node_client, action_name)
                value = action(**self.shared_lookup(node_args))

                print(indent(json.dumps(value, indent=2,
                      default=str), '+ ', lambda _: True))

                rsetattr(
                    context=self.ir,
                    accessor=f"{resource_name}.{action_name}",
                    value=value,
                )
            except Exception as e:
                print(indent(json.dumps(e, indent=2, default=str),
                      '- ', lambda _: True))


def main():
    parser = argparse.ArgumentParser(description='Create an awyes deployment')

    parser.add_argument('--workflow', type=str, required=True,
                        help='The awyes workflow type')
    parser.add_argument('--path', type=str, required=False,
                        default="awyes.yml", help='Path to awyes config')
    parser.add_argument('--config', type=str, required=False, default="",
                        help='Raw config to use in place of path')
    parser.add_argument('--preview', action=argparse.BooleanOptionalAction)

    Deployment(**vars(parser.parse_args())).deploy()


if __name__ == '__main__':
    main()
