
def deploy_events(self):
    for event_config in self.config['events']:
        rule = None

        try:
            rule = self.__class__.event_client.describe_rule(
                Name=event_config['name']
            )
        except Exception as e:
            print(e)

            rule = self.__class__.event_client.put_rule(
                Name=event_config['name'],
                ScheduleExpression=event_config['expression'],
                Description=event_config['description'],
            )

        self.shared['events'][event_config['name']] = rule
