# awyes

## Action

Deploy infra trivially to AWS. Yas.

### Inputs

- #### `config`
  The path to your awyes.yml. Defaults to `./awyes.yml`. Required
- #### `clients`
  The path to your clients file. Defaults to `./awyes.py`. Not required, awyes includes boto3 client by default
- #### `workflow`
  Required. The workflow describing a subselection of nodes intended to run. Defaults to `init`.

### Usage

```
uses: bb-labs/awyes@main # or pin to latest major
with:
  config: '/path/to/your/projects/awyes.yml'
  clients: '/path/to/your/projects/awyes.py'
  workflow: init
```

## An `awyes.yml` file

```
# # -------------------------------------------------------------------
# # roles
# # -------------------------------------------------------------------
pastewin_role:
  get_role:
    client: iam
    depends_on:
      - pastewin_role.create_role
    workflow:
      - init
    args:
      RoleName: pastewin
  create_role:
    client: iam
    workflow:
      - init
    args:
      RoleName: pastewin
      Description: Role for pastewin
      AssumeRolePolicyDocument: >
        {
          "Version": "2012-10-17",
          "Statement": [{
            "Effect": "Allow",
            "Principal": { "Service": "lambda.amazonaws.com" },
            "Action": "sts:AssumeRole"
          }]
        }

pastewin_role_attach_cloud:
  attach_role_policy:
    client: iam
    depends_on:
      - pastewin_role.get_role
    workflow:
      - init
    args:
      RoleName: pastewin
      PolicyArn: arn:aws:iam::aws:policy/CloudWatchFullAccess

pastewin_role_attach_s3:
  attach_role_policy:
    client: iam
    depends_on:
      - pastewin_role.get_role
    workflow:
      - init
    args:
      RoleName: pastewin
      PolicyArn: arn:aws:iam::aws:policy/AmazonS3FullAccess
```
