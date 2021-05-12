from pprint import pprint
from os.path import normpath, join


def deploy_images(self):
    for dockerfile in self.images:
        self.__class__.docker_client.build(
            decode=True,
            path=self.root_path,
            dockerfile=normpath(join(
                self.root_path,
                self.config_path,
                dockerfile
            ))
        )

    pprint(self.__class__.docker_client.images())
