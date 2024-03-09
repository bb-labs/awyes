import re
import json
import types
import textwrap
import collections

from .utils import rgetattr, rsetattr, Colors
from .constants import (
    DOT,
    MATCH_REF,
    CACHE_REGEX,
    USER_CLIENT_MODULE_NAME,
)


class Deployment:
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
                CACHE_REGEX,
                lambda m: rgetattr(self.cache, m.group(MATCH_REF)),
                json.dumps(args, sort_keys=True),
            )
        )

    def find_recursive_actions(self, args):
        """Look through the args dict and find all actions for cache references."""
        return [
            DOT.join(action_prefixes)
            for cache_reference in re.findall(
                CACHE_REGEX, json.dumps(args, sort_keys=True)
            )
            for action_prefixes in [
                cache_reference.split(DOT)[:i]
                for i, _ in enumerate(cache_reference.split(DOT))
            ]
            if DOT.join(action_prefixes) in self.config
        ]

    def run(self, actions):
        """Run the deployment."""
        for action in actions:
            self.execute(action)

    # `action` is a str of form <one>.<or>.<more>.<namespaces>.<client>.<fn>
    def execute(self, action, seen=set()):
        """Execute an action."""
        # Split the action into its components
        *namespace, client_name, fn_name = action.split(DOT)
        id = f"{'.'.join(namespace)}.{client_name}.{fn_name}"

        # If we've already seen this action when recursing, return
        if id in seen:
            return
        else:
            seen.add(id)

        # Execute actions recursively
        for dep_action in self.find_recursive_actions(self.config[action]):
            self.execute(dep_action, seen)

        # Print the action
        print(f"{Colors.OKCYAN}{id}{Colors.ENDC}")

        # Try to get the function from the client
        try:
            fn = rgetattr(
                self.clients,
                (
                    fn_name
                    if client_name == USER_CLIENT_MODULE_NAME
                    else f"{client_name}.{fn_name}"
                ),
            )
        except Exception as e:
            self.print_status("Could not resolve function", Colors.FAIL, "✗")
            self.print_status(e, Colors.FAIL, "✗")
            return

        # If we're not quiet and are dry running, print the unresolved args
        if self.flags.dry:
            if not self.flags.quiet:
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

        # If we're not quiet, print the resolved args
        if not self.flags.quiet:
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

        # If we're not quiet, print the result
        if not self.flags.quiet:
            self.print_status(value, Colors.OKGREEN, "✓")

        # Try to cache the result
        try:
            rsetattr(self.cache, id, value)
        except Exception as e:
            self.print_status("Could not cache result", Colors.FAIL, "✗")
            self.print_status(e, Colors.FAIL, "✗")
            return
