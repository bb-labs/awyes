import re
import json
import types

from copy import deepcopy
from textwrap import indent

from .utils import rgetattr, rsetattr, rhasattr, Colors


class Cache(dict):
    def resolve(self, args):
        if isinstance(args, dict):
            for key, value in args.items():
                args[key] = self.resolve(value)

            return args

        if isinstance(args, list):
            return list(map(lambda value: self.resolve(value), args))

        if isinstance(args, bytes):
            return args.decode()

        if isinstance(args, str):
            match = re.search("\$\((?P<reference>.*)\)", args)

            if not match:
                return args

            value = self.resolve(rgetattr(self, match.group("reference")))

            return re.sub(re.escape(match.group()), value, args) \
                if isinstance(value, str) else value

        return args


class Deployment:
    def __init__(self, verbose, preview, config, clients):
        self.config = config
        self.clients = clients
        self.cache = Cache(deepcopy(self.config))

        self.verbose = verbose
        self.preview = preview

    def get_fully_qualified_node_names(self):
        return [f"{resource_name}.{action_name}"
                for resource_name, actions in self.config.items()
                for action_name in actions.keys()]

    def get_topologically_sorted_nodes(self):
        sorted_nodes = []

        for node_name in self.get_fully_qualified_node_names():
            self.visit_parents(node_name, sorted_nodes=sorted_nodes)

        return sorted_nodes

    def visit_parents(self, node_name, seen=set(), sorted_nodes=[]):
        if node_name in seen:
            return

        node = rgetattr(self.config, node_name)

        if not rhasattr(node, "workflow"):
            raise Exception(
                f"{node_name} is missing workflow tags.")

        if rhasattr(node, "args") and rgetattr(node, 'args') is None:
            raise f"args should not be none for {node_name}"

        node.setdefault("args", {})
        node.setdefault("secret", False)
        node.setdefault("name", node_name)
        node.setdefault("depends_on", [])

        seen.add(node_name)

        for parent_node_name in node.get("depends_on"):
            self.visit_parents(parent_node_name, seen, sorted_nodes)

        sorted_nodes.append(node)

        return sorted_nodes

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

    def execute(self, node):
        node_args = rgetattr(node, "args")
        node_name = rgetattr(node, "name")
        node_secret = rgetattr(node, "secret")
        node_client = rgetattr(self.clients, rgetattr(node, "client"))
        resource_name, action_name = node_name.split(".")

        if self.verbose:
            print(f"{Colors.OKCYAN}{node_name}{Colors.ENDC}")
        try:
            args = self.cache.resolve(node_args)
            action = rgetattr(node_client, action_name)

            if isinstance(args, list):
                value = action(*args)
            elif isinstance(args, dict):
                value = action(**args)

            if isinstance(value, types.GeneratorType):
                value = list(value)  # auto unpack generators

            if self.verbose and not node_secret:
                self.print_status(value, Colors.OKGREEN)

            rsetattr(
                context=self.cache,
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
