from re import sub
from pprint import pprint
from os.path import normpath, join


def deploy_images(self):
    client = self.__class__.docker_client

    for dockerfile in self.images:
        image_name = sub(".Dockerfile", "", dockerfile)
        remote_tag = f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com/{image_name}"

        image, *_ = client.images.build(
            tag=image_name,
            path=self.root_path,
            dockerfile=normpath(join(
                self.root_path,
                self.config_path,
                dockerfile
            ))
        )

        image.tag(repository=remote_tag)

        pprint([line for line in client.images.push(repository=remote_tag)])
