# awyes

## Action
Deploy infra trivially to AWS. Yas.

### Inputs

#### `path`
The directory containing your awyes.yml. Defaults to `./awyes.yml`.

### Usage
```
uses: actions/awyes@v1
with:
  path: '/path/to/your/projects/awyes.yml'
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
    args:
      RoleName: pastewin
  create_role:
    client: iam
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
    args:
      RoleName: pastewin
      PolicyArn: arn:aws:iam::aws:policy/CloudWatchFullAccess

pastewin_role_attach_s3:
  attach_role_policy:
    client: iam
    depends_on:
      - pastewin_role.get_role
    args:
      RoleName: pastewin
      PolicyArn: arn:aws:iam::aws:policy/AmazonS3FullAccess
```