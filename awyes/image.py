from operator import itemgetter
from re import sub
from pprint import pprint
from os.path import normpath, join


def deploy_images(self):
    # Localize the clients
    ecr = self.__class__.ecr_client
    docker = self.__class__.docker_client

    # Check if an ecr repository exists, if not create one
    for repo_name in self.config['repositories']:
        try:
            description = ecr.describe_repositories(
                registryId=self.account_id,
                repositoryNames=[repo_name]
            )

            repository = description['repositories'].pop()
        except:
            response = ecr.create_repository(repositoryName=repo_name)
            repository = response['repository']

        self.shared['ecr'][repo_name] = repository

    # Build the images for each lambda
    for dockerfile in self.images:
        image_name = sub(".Dockerfile", "", dockerfile)
        remote_repository = f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com/{image_name}"

        image, *_ = docker.images.build(
            tag=image_name,
            path=self.root_path,
            dockerfile=normpath(join(
                self.root_path,
                self.config_path,
                dockerfile
            ))
        )

        image.tag(repository=remote_repository, tag=image_name)
        print(docker.images.push(repository=remote_repository, tag=image_name))
