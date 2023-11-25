import os
import os.path
import sys
import yaml
import dotenv
import argparse
import pathlib
import itertools
import subprocess
import importlib
import importlib.util
import pipreqs.pipreqs
import awyes.deploy

USER_CLIENT_NAME = "user"


def load_config(config_path):
    with open(os.path.normpath(config_path)) as config:
        config, workflows = yaml.safe_load_all(
            os.path.expandvars(config.read()))

    return config, workflows


def load_env(env_path, overrides):
    dotenv.load_dotenv(os.path.normpath(env_path))
    if overrides:
        os.environ.update(dict(map(lambda var: var.split("="),
                               itertools.chain(*overrides))))


def inject_clients(client_path):
    user_client_path = pathlib.Path(client_path).resolve()

    # Figure out / install the requirements from user provided script
    requirements = pipreqs.pipreqs.get_pkg_names(
        pipreqs.pipreqs.get_all_imports(user_client_path.parent))

    subprocess.run([sys.executable, "-m", "pip", "install", *requirements],
                   stdout=subprocess.DEVNULL, check=True)

    # Inject the user provided clients into sys.modules
    spec = importlib.util.spec_from_file_location(
        USER_CLIENT_NAME, user_client_path)
    user_client = importlib.util.module_from_spec(spec)
    sys.modules[USER_CLIENT_NAME] = user_client
    spec.loader.exec_module(user_client)

    return sys.modules[USER_CLIENT_NAME]


def get_actions(config, workflow):
    return [[action_label] if isinstance(action_label, dict)
            else [{action_name: action} for action_name, action in config.items() if action_label in action_name]
            for action_label in workflow]


def get_arguments():
    parser = argparse.ArgumentParser(description='Create an awyes deployment')

    parser.add_argument(
        '-p', '--preview', action=argparse.BooleanOptionalAction, default=False,
        help="Whether or not to execute the plan")
    parser.add_argument(
        '-v', '--verbose', action=argparse.BooleanOptionalAction, default=True,
        help="Enable logging")
    parser.add_argument('-w', '--workflow', type=str,
                        required=True, help='The workflow type')
    parser.add_argument('-s', '--set', action='append', nargs='+')
    parser.add_argument('-e', '--env', type=str, required=False,
                        default=".env", help='Path to env')
    parser.add_argument('--config', type=str, required=False,
                        default="awyes.yml", help='Path to config')
    parser.add_argument('--clients', type=str, required=False,
                        default="awyes.py",
                        help='Path to user specified clients')

    return parser.parse_args()


def main():
    # Get the cli arguments
    args = get_arguments()

    # Load the env
    try:
        load_env(args.env, args.set)
    except:
        print(f"WARNING: could not load env {args.env}, using system env.")

    # Load the config
    try:
        config, workflows = load_config(args.config)
    except:
        raise "couldn't parse config. You must pass a two part yaml file: the first part: config, the second part: workflows."

    # Validate workflow
    if not workflows.get(args.workflow):
        raise "couldn't find workflow {} in config.".format(args.workflow)

    # Inject the user provided clients
    try:
        clients = inject_clients(args.clients)
    except Exception:
        raise "couldn't find any provided clients at: {}.".format(args.clients)

    # Create and run the deployment
    actions = get_actions(config, workflows.get(args.workflow))
    awyes.deploy.Deployment(args.verbose, args.preview,
                            config, clients).run(itertools.chain(*actions))


if __name__ == '__main__':
    main()
