def deploy_lambdas(self):
    # Loop through the lambdas
    for lambda_config in self.config['lambdas']:
        lmbda = None

    # Grab the lambda
    try:
        lmbda = self.__class__.lambda_client.get_function(
            FunctionName=lambda_config['name']
        )
    except:
        lmbda = self.__class__.lambda_client.create_function(
            FunctionName=lambda_config['name'],
            Handler=lambda_config['handler'],
            Runtime=lambda_config['runtime'],
            Layers=[
                layer['LayerVersionArn']
                for layer in map(lambda name: shared['layers'][name], lambda_config['layers'])
            ],
            Role=shared['roles'][lambda_config['role']]['Arn'],
            Code={
                'ZipFile': open(f"./{lambda_config['source']}.zip", 'rb').read()
            }
        )

    # Update the function code
    self.__class__.lambda_client.update_function_code(
        FunctionName=lambda_config['name'],
        ZipFile=open(f"./{lambda_config['source']}.zip", 'rb').read()
    )

    # Update the function configuration
    self.__class__.lambda_client.update_function_configuration(
        FunctionName=lambda_config['name'],
        Handler=lambda_config['handler']
    )

    # Attach events to the lambda
    for event_name in lambda_config['events']:
        event = shared['events'][event_name]

        try:
            self.__class__.event_client.put_targets(
                Rule=event['Name'],
                Targets=[{
                    'Id': lambda_config['name'],
                    'Arn': lmbda['Configuration']['FunctionArn']
                }]
            )

            self.__class__.lambda_client.add_permission(
                FunctionName=lambda_config['name'],
                SourceArn=event['Arn'],
                StatementId=event['Name'],
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
            )

        except:  # Already gave permission and added targets
            pass
