import json


def deploy_roles(self):
    role = None

    for role_config in self.config['roles']:
        try:
            role = self.__class__.iam_client.get_role(
                RoleName=role_config['name']
            )
        except Exception as e:
            print(e)

            role = self.__class__.iam_client.create_role(
                RoleName=role_config['name'],
                Description=role_config['description'],
                AssumeRolePolicyDocument=json.dumps(role_config['trust']),
            )

        for policy in role_config['policies']:
            try:
                self.__class__.iam_client.attach_role_policy(
                    RoleName=role_config['name'],
                    PolicyArn=policy
                )
            except Exception as e:  # already attached this policy
                print(e)

    self.shared['roles'][role_config['name']] = role['Role']
