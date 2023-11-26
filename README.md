# awyes

## Action

`awyes` lets you define a series of `action`s (functions) in yaml format, and run them as part of larger workflows. It's CI/CD, bro.

### Inputs

- #### `config`
  The path to your awyes.yml. Defaults to `awyes.yml`. Optional.
- #### `clients`
  The path to your clients file. Defaults to `awyes.py`. Optional.
- #### `deps`
  The path to your deps file. Defaults to `awyes.txt`. Optional.
- #### `env`
  The env file describing env you wish to include your workflows. Defaults to `.env`. Optional.
- #### `workflow`
  The workflow describing a subselection of nodes intended to run. Required.

### Usage

```
uses: bb-labs/awyes@main # or pin to latest major
with:
  config: '/path/to/your/project/awyes.yml'
  clients: '/path/to/your/project/awyes.py'
  deps: '/path/to/your/project/awyes.txt'
  workflow: init
```

## First the clients `awyes.py`

Any clients you import will be automagically interpreted and installed by awyes. For every `action` (function) you wish to leverage in `awyes.yml`, you'll need to provide an export for. User-provided clients must go in a dict called `user`.

```
import os
import boto3
import yaml
import docker
import itertools
import subprocess


def deploy(action, account_id, region, cluster_name):
    # Inline utility functions
    def str_presenter(dumper, data):
        if len(data.splitlines()) > 1:
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)

    def wait_and_kill(proc):
        proc.wait()
        proc.kill()

    # Update kubeconfig auth to talk to the cluster
    wait_and_kill(subprocess.Popen(["aws", "eks", "update-kubeconfig",
                                    "--region", region, "--name", cluster_name], env=os.environ))

    yaml.add_representer(str, str_presenter)
    yaml.representer.SafeRepresenter.add_representer(str, str_presenter)

    auth = {
        "apiVersion": "v1",
        "data": {"mapUsers": f"- groups:\n  - system:masters\n  userarn: arn:aws:iam::{account_id}:root"},
        "kind": "ConfigMap",
        "metadata": {"name": "aws-auth", "namespace": "kube-system"}
    }

    with open('./kube/auth.yaml', 'w') as outfile:
        yaml.dump(auth, outfile)

    wait_and_kill(subprocess.Popen(
        ["kubectl",  "apply", "-f", "./kube/auth.yaml"]))

    # Install Helm charts
    env_args = list(itertools.chain(
        *[['--set', f'{k}={v}'] for k, v in os.environ.items()]))

    wait_and_kill(subprocess.Popen(
        ["helm", action, *env_args, cluster_name, "./kube"]))


user = {
    "deploy": deploy,
}
iam = boto3.client('iam')
ec2 = boto3.client('ec2')
eks = boto3.client('eks')
docker = docker.client.from_env()

```

## An `awyes.yml` file

The format of an `action` (backed by functions in the awyes.py file) is `<namespace>.<action_name>.<fn_name>.<metatag>`. The `metatag` is optional, and used solely to differentiate between otherwise identically named `action`s.

```
image.docker.build:
  tag: ${DOCKER_REGISTRY}/${APP_REPO}
  path: go
  dockerfile: Dockerfile
image.docker.push:
  repository: ${DOCKER_REGISTRY}/${APP_REPO}
  tag: ${APP_IMAGE_TAG}
  auth_config:
    username: ${DOCKER_HUB_USERNAME}
    password: ${DOCKER_HUB_PASSWORD}

node_role.iam.create_role:
  RoleName: ${APP_NODE_ROLE_NAME}
  Description: Role for sage kubernetes node
  AssumeRolePolicyDocument: >
    {
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {
          "Service": [
            "ec2.amazonaws.com"
          ]
        },
        "Action": "sts:AssumeRole"
      }]
    }
node_role.iam.get_role:
  RoleName: ${APP_NODE_ROLE_NAME}
node_role.iam.attach_role_policy.eks:
  RoleName: ${APP_NODE_ROLE_NAME}
  PolicyArn: arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy
node_role.iam.attach_role_policy.ec2:
  RoleName: ${APP_NODE_ROLE_NAME}
  PolicyArn: arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
node_role.iam.attach_role_policy.cni:
  RoleName: ${APP_NODE_ROLE_NAME}
  PolicyArn: arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy

cluster_role.iam.create_role:
  RoleName: ${APP_CLUSTER_ROLE_NAME}
  Description: Role for sage kubernetes cluster
  AssumeRolePolicyDocument: >
    {
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {
          "Service": [
            "lambda.amazonaws.com",
            "rds.amazonaws.com",
            "eks.amazonaws.com"
          ]
        },
        "Action": "sts:AssumeRole"
      }]
    }
cluster_role.iam.get_role:
  RoleName: ${APP_CLUSTER_ROLE_NAME}
cluster_role.iam.attach_role_policy:
  RoleName: ${APP_CLUSTER_ROLE_NAME}
  PolicyArn: arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

kube.ec2.describe_vpcs:
kube.ec2.describe_subnets:
  Filters:
    - Name: vpc-id
      Values:
        - $(kube.ec2.describe_vpcs.Vpcs.0.VpcId)
kube.ec2.describe_security_groups:
  GroupNames:
    - default
kube.eks.create_cluster:
  name: ${APP_CLUSTER_NAME}
  version: ${AWS_EKS_VERSION}
  roleArn: $(cluster_role.iam.get_role.Role.Arn)
  resourcesVpcConfig:
    securityGroupIds:
      - $(kube.ec2.describe_security_groups.SecurityGroups.0.GroupId)
    subnetIds:
      - $(kube.ec2.describe_subnets.Subnets.0.SubnetId)
      - $(kube.ec2.describe_subnets.Subnets.1.SubnetId)
      - $(kube.ec2.describe_subnets.Subnets.2.SubnetId)
      - $(kube.ec2.describe_subnets.Subnets.3.SubnetId)
    endpointPublicAccess: true
kube.eks.create_nodegroup:
  clusterName: sage
  nodegroupName: ${APP_NODE_GROUP_NAME}
  nodeRole: $(node_role.iam.get_role.Role.Arn)
  subnets:
    - $(kube.ec2.describe_subnets.Subnets.0.SubnetId)
    - $(kube.ec2.describe_subnets.Subnets.1.SubnetId)
    - $(kube.ec2.describe_subnets.Subnets.2.SubnetId)
    - $(kube.ec2.describe_subnets.Subnets.3.SubnetId)
kube.user.deploy:
  action: install
  account_id: ${AWS_ACCOUNT_ID}
  cluster_name: ${APP_CLUSTER_NAME}

---
vpcs:
  - kube.ec2.describe_vpcs
  - kube.ec2.describe_subnets

init:
  - image
  - node_role
  - cluster_role
  - kube

release:
  - image
  - kube.user.deploy:
      action: upgrade
      account_id: ${AWS_ACCOUNT_ID}
      cluster_name: ${APP_CLUSTER_NAME}
```
