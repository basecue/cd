from codev.task import Task
from codev.providers.tasks import AnsibleTask
import unittest

test_perfomer = None


class TaskTestCase(unittest.TestCase):
    def setUp(self):
        self.ansible_task = Task('ansible', test_perfomer, {})

    def test_ansible(self):
        self.assertEqual(self.ansible_task.__class__, AnsibleTask)


if __name__ == '__main__':
    unittest.main()
