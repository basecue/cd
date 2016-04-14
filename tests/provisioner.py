from codev.provisioner import Provisioner
from codev.providers.provisioners import AnsibleProvisioner
import unittest

test_perfomer = None


class ProvisionerTestCase(unittest.TestCase):
    def setUp(self):
        self.ansible_provisioner = Provisioner('ansible', test_perfomer, {})

    def test_ansible(self):
        self.assertEqual(self.ansible_provisioner.__class__, AnsibleProvisioner)


if __name__ == '__main__':
    unittest.main()
