import re
import boto3
import base64
import awyes.utils


def get_ecr_password():
    ecr = boto3.client('ecr')
    token_response = ecr.get_authorization_token()

    token = awyes.utils.rgetattr(
        token_response, 'authorizationData.0.authorizationToken')

    return re.sub("AWS:", "", base64.b64decode(token).decode())
