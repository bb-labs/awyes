import re
import os
import os.path
import sys
import yaml
import dotenv
import argparse
import pipfile
import pathlib
import subprocess
import collections
import importlib.util

from .deploy import Deployment
from .constants import (
    NEW_LINE,
    USER_ENV_PATH,
    USER_PIPFILE_PATH,
    USER_PIPFILE_INSTALL_COMMAND,
    USER_CLIENT_MODULE_NAME,
    USER_CLIENT_PATH_PREFIXES,
    USER_CLIENT_PATH_SUFFIXES,
    USER_CONFIG_PATH_PREFIXES,
    USER_CONFIG_PATH_SUFFIXES,
)


def load_config(path):
    collapse = lambda dl: dict(collections.ChainMap(*dl))

    return collapse(
        collapse(reversed(list(yaml.safe_load_all(os.path.expandvars(p.read_text())))))
        for p in pathlib.Path(path).resolve().rglob(USER_CONFIG_PATH_PREFIXES)
        if p.suffix in USER_CONFIG_PATH_SUFFIXES
    )


def load_env(path):
    return [
        dotenv.load_dotenv(p) for p in pathlib.Path(path).resolve().rglob(USER_ENV_PATH)
    ]


def load_clients(path):
    # Install the user's dependencies
    for dep, meta in (
        pipfile.load(pathlib.Path(os.path.join(path, USER_PIPFILE_PATH)).resolve())
        .data["default"]
        .items()
    ):
        subprocess.run(
            [
                sys.executable,
                *USER_PIPFILE_INSTALL_COMMAND,
                f"git+{meta['git']}" if "git" in meta else dep,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )

    # Inject the user provided module(s) into sys.modules
    spec = importlib.util.spec_from_loader(USER_CLIENT_MODULE_NAME, loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(
        NEW_LINE.join(
            [
                p.read_text()
                for p in pathlib.Path(path).resolve().rglob(USER_CLIENT_PATH_PREFIXES)
                if p.suffix in USER_CLIENT_PATH_SUFFIXES
            ]
        ),
        module.__dict__,
    )
    sys.modules[USER_CLIENT_MODULE_NAME] = module
    globals()[USER_CLIENT_MODULE_NAME] = module
    return sys.modules[USER_CLIENT_MODULE_NAME]


def get_actions(config, regexes):
    if not (
        actions := [
            action
            for regex in regexes
            for action in config.keys()
            if re.search(regex, action)
        ]
    ):
        raise ValueError(f"no actions found. Received: {regexes}")

    return actions


def get_arguments():
    parser = argparse.ArgumentParser(description="Run awyes actions")

    parser.add_argument(
        "-d",
        "--dry",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Preview the actions without running them",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Only show the action names",
    )
    parser.add_argument(
        "-p",
        "--path",
        type=str,
        required=False,
        default=".",
        help="Path to user pipfile",
    )
    parser.add_argument(
        "actions", type=str, metavar="N", nargs="+", help="The actions to run"
    )

    return parser.parse_args()


def main():
    # Get the cli arguments
    args = get_arguments()

    try:
        load_env(args.path)
        config = load_config(args.path)
        clients = load_clients(args.path)
        actions = get_actions(config, args.actions)

        Deployment(args, config, clients).run(actions)
    except:
        raise


if __name__ == "__main__":
    main()
