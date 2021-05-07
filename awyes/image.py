
def deploy_images(self):
    for dockerfile in self.images:
        print([
            line for line in
            self.__class__.docker_client.build(
                fileobj=open(self.root + '/' + dockerfile, 'rb')
            )
        ])
