from .utils import hash_file, hash_url


def publish_layer_version(self, layer_config):
    return self.__class__.lambda_client.publish_layer_version(
        LayerName=layer_config['name'],
        Description=layer_config['description'],
        CompatibleRuntimes=layer_config['runtimes'],
        Content={
            "ZipFile": open(f"./layers/{layer_config['name']}.zip", 'rb').read()
        },
    )


def deploy_layers(self):
    for layer_config in self.config['layers']:
        layer = None

        try:  # try getting the layer
            layer_version = self.__class__.lambda_client.list_layer_versions(
                LayerName=layer_config['name']
            )['LayerVersions'].pop(0)['Version']

            layer = self.__class__.lambda_client.get_layer_version(
                LayerName=layer_config['name'],
                VersionNumber=int(layer_version)
            )

        except Exception as e:  # layer doesn't exist, create it
            print(e)

            layer = publish_layer_version(self, layer_config)

        # Check the hash content: if they're different, publish anew
        old_digest = str(hash_url(layer['Content']['Location']))
        new_digest = str(hash_file(f"./layers/{layer_config['name']}.zip"))

        if new_digest != old_digest:
            layer = publish_layer_version(self, layer_config)

        self.shared['layers'][layer_config['name']] = layer
