import os
import re
import boto3
import docker
import yaml

from sys import argv
from os.path import normpath

from .utils import rgetattr, rsetattr


class Deployment:
    def __init__(self, paths=[], verbose=False):
        # Initialize paths and log settings
        self.paths = paths
        self.verbose = verbose

        # Load the config and docker images
        for path in self.paths:
            try:
                with open(normpath(path)) as config:
                    self.config = yaml.safe_load(config)
                    self.clients = {
                        "os": os,
                        "s3": boto3.client("s3"),
                        "ecr": boto3.client("ecr"),
                        "sts": boto3.client("sts"),
                        "iam": boto3.client("iam"),
                        "events": boto3.client("events"),
                        "lambda": boto3.client("lambda"),
                        "session": boto3.session.Session(),
                        "docker": docker.client.from_env(),
                    }

                break  # success
            except Exception as _:
                pass

        if not self.config:
            raise "Could not resolve of awyes.yml config"

    def get_fully_qualified_node_names(self):
        return [f"{resource_name}.{action_name}"
                for resource_name, actions in self.config.items()
                for action_name in actions.keys()]

    def get_topologically_sorted_nodes(self, seen=set(), sorted_nodes=[]):
        for node_name in self.get_fully_qualified_node_names():
            def visit_parents(node_name):
                node = rgetattr(self.config, node_name)

                node.setdefault("name", node_name)
                node.setdefault("args", {})
                node.setdefault("depends_on", [])

                seen.add(node_name)

                for parent_node_name in node.get("depends_on"):
                    visit_parents(parent_node_name)

                sorted_nodes.append(node)

            if node_name not in seen:
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
            name = getattr(node, "name")
            args = getattr(node, "args")
            client = getattr(node, "client")

            resource_name, action_name = name.split(".")

            try:
                action = getattr(client, action_name)
                value = action(**self.shared_lookup(args))

                if self.verbose:
                    print(f"setting value {value} for {name}")

                rsetattr(
                    context=self.config,
                    accessor=f"{resource_name}.{action_name}",
                    value=value,
                )
            except Exception as e:
                print("err: ", e)


def main():
    _, *path = argv
    path = path[0] if path else ["./awyes.yml", "./awyes.yaml", "./awyes"]

    Deployment(path=path).deploy()


if __name__ == '__main__':
    main()
