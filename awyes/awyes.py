import os
import re
import boto3
import docker
import yaml
import json

from sys import argv
from textwrap import indent
from os.path import normpath

from .utils import rgetattr, rsetattr


class Deployment:
    def __init__(self, path="", config=""):
        self.path = path

        self.config = yaml.safe_load(config)
        if not self.config:
            with open(normpath(path)) as config:
                self.config = yaml.safe_load(config)

        self.clients = {
            "os": os,
            "s3": boto3.client("s3"),
            "ecr": boto3.client("ecr"),
            "sts": boto3.client("sts"),
            "rds": boto3.client("rds"),
            "iam": boto3.client("iam"),
            "events": boto3.client("events"),
            "lambda": boto3.client("lambda"),
            "session": boto3.session.Session(),
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

        if isinstance(args, str):
            match = re.search("\$\((?P<reference>.*)\)", args)

            if not match:
                return args

            value = rgetattr(self.config, match.group("reference"))

            if isinstance(value, str):
                return re.sub(re.escape(match.group()), value, args)

            return value

        return args

    def deploy(self):
        for node in self.get_topologically_sorted_nodes():
            node_name = rgetattr(node, "name")
            node_args = rgetattr(node, "args")
            node_client = rgetattr(self.clients, rgetattr(node, "client"))

            resource_name, action_name = node_name.split(".")

            print(f"\033[36m{node_name}\033[0m")

            try:
                action = rgetattr(node_client, action_name)
                value = action(**self.shared_lookup(node_args))

                print(indent(json.dumps(value, indent=2,
                      default=str), '+ ', lambda _: True))

                rsetattr(
                    context=self.config,
                    accessor=f"{resource_name}.{action_name}",
                    value=value,
                )
            except Exception as e:
                print(indent(json.dumps(e, indent=2, default=str),
                      '- ', lambda _: True))


def main():
    _, *path = argv
    path = path[0] if path else "./awyes.yml"

    Deployment(path=path).deploy()


if __name__ == '__main__':
    main()
