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
import importlib
import importlib.util
import awyes.deploy


USER_CLIENT_NAME = "user"


def load_config(config_path):
    with open(os.path.normpath(config_path)) as config:
        return dict(
            collections.ChainMap(*yaml.safe_load_all(os.path.expandvars(config.read())))
        )


def load_env(env_path):
    return dotenv.load_dotenv(os.path.normpath(env_path))


def load_clients(client_path, pipfile_path):
    # Install the user's dependencies
    for dep, meta in pipfile.load(pipfile_path).data["default"].items():
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                f"git+{meta['git']}" if "git" in meta else dep,
            ],
            stdout=subprocess.DEVNULL,
            check=True,
        )

    # Inject the user provided clients into sys.modules
    spec = importlib.util.spec_from_file_location(
        USER_CLIENT_NAME, pathlib.Path(client_path).resolve()
    )
    user_client = importlib.util.module_from_spec(spec)
    sys.modules[USER_CLIENT_NAME] = user_client
    spec.loader.exec_module(user_client)

    return sys.modules[USER_CLIENT_NAME]


def get_actions(config, regexes):
    return [
        action
        for regex in regexes
        for action in config.keys()
        if re.search(regex, action)
    ]


def get_arguments():
    parser = argparse.ArgumentParser(description="Run awyes actions")

    parser.add_argument(
        "-p",
        "--preview",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Preview the actions without running them",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Print verbose output",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Find and run all dependent actions recursively",
    )
    parser.add_argument(
        "-e", "--env-path", type=str, required=False, default=".env", help="Path to env"
    )
    parser.add_argument(
        "-g",
        "--config-path",
        type=str,
        required=False,
        default="awyes.yml",
        help="Path to config",
    )
    parser.add_argument(
        "-l",
        "--client-path",
        type=str,
        required=False,
        default="awyes.py",
        help="Path to user specified clients",
    )
    parser.add_argument(
        "-d",
        "--pipfile-path",
        type=str,
        required=False,
        default="Pipfile",
        help="Path to user pipfile",
    )
    parser.add_argument(
        "actions", type=str, metavar="N", nargs="+", help="The actions to run"
    )

    return parser.parse_args()


def main():
    # Get the cli arguments
    args = get_arguments()

    # Load the env
    try:
        load_env(args.env_path)
    except:
        print(f"WARNING: could not load env {args.env_path}, using system env.")

    # Load the config
    config = load_config(args.config_path)

    # Inject the user provided clients
    try:
        clients = load_clients(args.client_path, args.pipfile_path)
    except:
        raise ValueError(f"couldn't find any clients at: {args.client_path}")

    # Create and run the deployment
    awyes.deploy.Deployment(args, config, clients).run(
        get_actions(config, args.actions)
    )


if __name__ == "__main__":
    main()
