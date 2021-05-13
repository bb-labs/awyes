from re import sub
from pprint import pprint
from os.path import normpath, join


def deploy_images(self):
    for dockerfile in self.images:
        image = sub(".Dockerfile", "", dockerfile)
        remote_tag = f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com/{image}"

        self.__class__.docker_client.build(
            decode=True,
            tag=image,
            path=self.root_path,
            dockerfile=normpath(join(
                self.root_path,
                self.config_path,
                dockerfile
            ))
        )

        self.__class__.docker_client.tag(image=image, repository=remote_tag)
        self.__class__.docker_client.push(repository=remote_tag)
