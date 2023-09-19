import sys
import yaml
import boto3
import docker
import os.path
import argparse
import pathlib
import importlib
import importlib.util
import awyes.deploy
import awyes.clients


USER_CLIENT_NAME = "user"


def main():
    parser = argparse.ArgumentParser(description='Create an awyes deployment')

    parser.add_argument(
        '--preview', action=argparse.BooleanOptionalAction, default=False,
        help="Whether or not to execute the plan")
    parser.add_argument(
        '--verbose', action=argparse.BooleanOptionalAction, default=True,
        help="Enable logging")
    parser.add_argument(
        '--include-deps', action=argparse.BooleanOptionalAction, default=False,
        help="When specifying an action, whether to include dependent actions")
    parser.add_argument(
        '--include-docker', action=argparse.BooleanOptionalAction,
        default=True,
        help="Include a docker client")

    parser.add_argument('--workflow', type=str, required=False, default="",
                        help='The awyes workflow type')
    parser.add_argument('--config', type=str, required=False,
                        default="awyes.yml", help='Path to awyes config')
    parser.add_argument('--clients', type=str, required=False, default="awyes.py",
                        help='Path to user specified awyes clients')
    parser.add_argument('--raw', type=str, required=False, default="",
                        help='Raw config to use in place of path')
    parser.add_argument('--action', type=str, required=False, default="",
                        help="A specific action to run")
    args = parser.parse_args()

    # Load the config
    config = yaml.safe_load(args.raw)
    if not config:
        with open(os.path.normpath(args.config)) as config:
            config = yaml.safe_load(config)

    # Resolve the clients
    clients = {
        "awyes": awyes.clients,
        "iam": boto3.client('iam'),
        "s3": boto3.client("s3"),
        "ecr": boto3.client("ecr"),
        "sts": boto3.client("sts"),
        "rds": boto3.client("rds"),
        "events": boto3.client("events"),
        "lambda": boto3.client("lambda"),
        "apigatewayv2": boto3.client('apigatewayv2'),
        "organizations": boto3.client("organizations"),
    }

    if args.include_docker:
        clients.update({"docker": docker.client.from_env()})

    try:
        user_client_path = pathlib.Path(args.clients).resolve()

        spec = importlib.util.spec_from_file_location(
            USER_CLIENT_NAME, user_client_path)
        user_client = importlib.util.module_from_spec(spec)
        sys.modules[USER_CLIENT_NAME] = user_client
        spec.loader.exec_module(user_client)

        clients.update({USER_CLIENT_NAME: user_client})
    except Exception:
        print("WARNING: couldn't find clients file. Using defaults")

    deployment = awyes.deploy.Deployment(args.verbose, args.preview,
                                         config, clients)
    if args.action:
        deployment.one_off(args.action, args.include_deps)
    elif args.workflow:
        deployment.deploy(args.workflow)
    else:
        raise "Please pass either a workflow tag or an action"


if __name__ == '__main__':
    main()
