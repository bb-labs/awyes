import re
import sys
import time
import json
import types
import collections
import rich.console

from .utils import rgetattr, rsetattr, print_status, Colors
from .constants import X, CHECK, ARROW, DOT, CACHE, MATCH, ANIMATION_SLEEP, NO_EXCEPTION


class Deployment:
    def __init__(self, flags, config, clients):
        """Initialize the deployment."""
        self.cache = (nested_dict := lambda: collections.defaultdict(nested_dict))()
        self.flags = flags
        self.config = config
        self.clients = clients

    @staticmethod
    def gen_action_prefixes(action):
        """
        Generate all prefixes of an action.
        e.g. 'a.b.c' -> [['a'], ['a', 'b'], ['a', 'b', 'c']].
        """
        return [action.split(DOT)[:i] for i in range(1, action.count(DOT) + 2)]

    @staticmethod
    def gen_action_suffixes(action):
        """
        Generate all suffixes of an action.
        e.g. 'a.b.c' -> [['c'], ['b', 'c'], ['a', 'b', 'c']].
        """
        return [action.split(DOT)[-i:] for i in range(1, action.count(DOT) + 2)]

    @staticmethod
    def cache_decoder(cache):
        """Generate a cache decoder class to properly preserve cache value types."""

        class CacheDecoder(json.JSONDecoder):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                def parse_string(*a, **ka):
                    s, e = json.decoder.scanstring(*a, **ka)
                    if m := re.fullmatch(CACHE, s):
                        return rgetattr(cache, m.group(MATCH)), e
                    if m := re.search(CACHE, s):
                        return re.sub(CACHE, rgetattr(cache, m.group(MATCH)), s), e
                    return s, e

                self.parse_string = parse_string
                self.scan_once = json.scanner.py_make_scanner(self)

        return CacheDecoder

    def resolve_args(self, args):
        """Resolve all cache references in the args dict."""
        return json.loads(json.dumps(args), cls=Deployment.cache_decoder(self.cache))

    def recurse_args(self, args):
        """Look through the args dict and find all actions for cache references."""
        return [
            action
            for cache_reference in re.findall(CACHE, json.dumps(args))
            for action_prefix in Deployment.gen_action_prefixes(cache_reference)
            if (action := DOT.join(action_prefix)) in self.config
        ]

    def resolve_action(self, action):
        """
        Resolve the callable from the action. e.g. 'a.b.c' -> b.c()
        """
        for action_suffixes in Deployment.gen_action_suffixes(action):
            try:
                return rgetattr(self.clients, action_suffixes)
            except:
                continue

        raise ValueError(f"no callable found for {action}")

    def run(self, actions):
        """Run the deployment."""
        for action in actions:
            self.execute(action)

    def execute(self, action, seen=set()):
        """Execute an action."""
        # If we've already seen this action when recursing, return
        if action in seen:
            return
        else:
            seen.add(action)

        # Execute actions recursively by parsing the args to find references
        for dep_action in self.recurse_args(self.config[action]):
            self.execute(dep_action, seen)

        with rich.console.Console().status(f"[bold grey]{action}"):
            try:
                # If we're dry running, bail.
                if self.flags.dry:
                    return

                # Animate the action running
                time.sleep(ANIMATION_SLEEP)

                # Lookup the one and only callable from the possible suffixes
                fn = self.resolve_action(action)

                # Try to resolve the args
                args = None
                args = self.resolve_args(self.config[action])

                # Try to execute the function
                value = None
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

                # Try to cache the result
                rsetattr(self.cache, action, value)
            except:
                print_status(action, Colors.FAIL, X)
                print_status(args, Colors.OKBLUE, ARROW) if args else None
                print_status(value, Colors.WARNING, CHECK) if value else None
                raise
            finally:
                if sys.exc_info() == NO_EXCEPTION:
                    # If we're dry running, print the action and the unresolved args
                    if self.flags.dry:
                        print_status(action, Colors.OKBLUE, CHECK)
                        print_status(self.config[action], Colors.OKCYAN, ARROW)
                        return
                    # If we're verbose, print the action, args, and value
                    elif self.flags.verbose:
                        print_status(action, Colors.OKGREEN, CHECK)
                        print_status(args, Colors.OKCYAN, ARROW) if args else None
                        print_status(value) if value else None
                    # Otherwise, just print the action
                    else:
                        print_status(action, Colors.OKGREEN, CHECK)
