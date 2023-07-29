import unittest
import yaml
from .awyes import Deployment
from .utils import rgetattr
from pprint import pprint


class DeploymentTestSuccess(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(DeploymentTestSuccess, self).__init__(*args, **kwargs)
        self.good_yaml = yaml.safe_load("./test_data/good.yml")

    def test_ordering_and_populated_fields(self):
        d = Deployment(path="./awyes/test_data/good.yml")
        sorted_nodes = d.get_topologically_sorted_nodes()
        self.assertEqual(sorted_nodes, [
            {
                'client': 'some_other_client',
                'args': {'another': 'argument'},
                'name': 'some_namespace.some_other_action',
                'depends_on': []
            },
            {
                'client': 'some_client',
                'depends_on': ['some_namespace.some_other_action'],
                'args': {'an': 'argument'},
                'name': 'some_namespace.some_action'
            }
        ])


if __name__ == "__main__":
    unittest.main()
