import re
import json
import types
import textwrap
import collections

from .utils import rgetattr, rsetattr, Colors


class Deployment:
    MATCH_REF = "reference"
    CACHE_REGEX = "\$\((?P<reference>.*?)\)"
    ACTION_REGEX = "^\w+\.\w+\.\w+"

    def __init__(self, flags, config, clients):
        """Initialize the deployment."""
        self.cache = (nested_dict := lambda: collections.defaultdict(nested_dict))()
        self.flags = flags
        self.config = config
        self.clients = clients

    def print_status(self, value, status, indicator):
        """Print a status message."""
        print(
            textwrap.indent(
                json.dumps(value, indent=2, default=str),
                f"{status}{indicator} {Colors.ENDC}",
                lambda _: True,
            )
        )

    def resolve(self, args):
        """Resolve all cache references in the args dict."""
        return json.loads(
            re.sub(
                Deployment.CACHE_REGEX,
                lambda m: rgetattr(self.cache, m.group(Deployment.MATCH_REF)),
                json.dumps(args, sort_keys=True),
            )
        )

    def find_recursive_actions(self, args):
        """Look through the args dict and find all actions for cache references."""
        return [
            re.findall(Deployment.ACTION_REGEX, cache_reference).pop()
            for cache_reference in re.findall(
                Deployment.CACHE_REGEX, json.dumps(args, sort_keys=True)
            )
        ]

    def run(self, actions):
        """Run the deployment."""
        for action in actions:
            self.execute(action)

    # `action` is a str of form <namespace>.<client>.<fn>
    def execute(self, action, seen=set()):
        """Execute an action."""
        # Split the action into its components
        *ns, client_name, fn_name = action.split(".")
        id = f"{'.'.join(ns)}.{client_name}.{fn_name}"

        # If we've already seen this action (in recursive mode), return
        if id in seen:
            return
        seen.add(id)

        # If the action is recursive, execute its dependencies first
        if self.flags.recursive:
            for dep_action in self.find_recursive_actions(self.config[action]):
                self.execute(dep_action, seen)

        # If the action is verbose or preview, print the action
        if self.flags.verbose or self.flags.preview:
            print(f"{Colors.OKCYAN}{id}{Colors.ENDC}")

        # Try to get the function from the client
        try:
            fn = rgetattr(
                self.clients,
                fn_name if client_name == "user" else f"{client_name}.{fn_name}",
            )
        except Exception as e:
            self.print_status("Could not resolve function", Colors.FAIL, "✗")
            self.print_status(e, Colors.FAIL, "✗")
            return

        # If the action is preview, print the unresolved args
        if self.flags.preview:
            self.print_status(self.config[action], Colors.OKBLUE, "→")
            return

        # Try to resolve the args
        try:
            args = self.resolve(self.config[action])
        except Exception as e:
            self.print_status("Could not resolve args", Colors.FAIL, "✗")
            self.print_status(self.config[action], Colors.FAIL, "✗")
            self.print_status(e, Colors.FAIL, "✗")
            return

        # If the action is verbose, print the resolved args
        if self.flags.verbose:
            self.print_status(args, Colors.OKBLUE, "→")

        # Try to execute the function
        try:
            if isinstance(args, dict):
                value = fn(**args)
            elif isinstance(args, list):
                value = fn(*args)
            elif args:
                value = fn(args)
            else:
                value = fn()

            # Auto-unpack generator results
            if isinstance(value, types.GeneratorType):
                value = list(value)
        except Exception as e:
            self.print_status("Could not execute function", Colors.FAIL, "✗")
            self.print_status(e, Colors.FAIL, "✗")
            return

        # If the action is verbose, print the result
        if self.flags.verbose:
            self.print_status(value, Colors.OKGREEN, "✓")

        # Try to cache the result
        try:
            rsetattr(self.cache, id, value)
        except Exception as e:
            self.print_status("Could not cache result", Colors.FAIL, "✗")
            self.print_status(e, Colors.FAIL, "✗")
            return
