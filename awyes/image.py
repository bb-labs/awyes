from pprint import pprint
from os.path import normpath


def deploy_images(self):
    for dockerfile in self.images:
        pprint([
            line for line in
            self.__class__.docker_client.build(
                decode=True,
                path=self.root_path,
                dockerfile=normpath(
                    self.root_path,
                    self.config_path,
                    dockerfile
                ),
            )
        ])
