import unittest
from .awyes import Deployment
from .utils import rgetattr


class DeploymentTestSuccess(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(DeploymentTestSuccess, self).__init__(*args, **kwargs)
        self.d = Deployment(path="./awyes/test_data/data.yml")

    def test_ordering_and_populated_fields(self):
        sorted_nodes = self.d.get_topologically_sorted_nodes()
        self.assertEqual([rgetattr(node, 'name') for node in sorted_nodes], [
            'pastewin_role.create_role',
            'pastewin_role.get_role',
            'pastewin_role_attach_cloud.attach_role_policy',
            'pastewin_role_attach_s3.attach_role_policy'
        ])

    def test_deploy(self):
        self.d.deploy()


if __name__ == "__main__":
    unittest.main()
