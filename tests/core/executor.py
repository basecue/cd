from codev.core import Performer
from codev.core.executor import Executor


class TestPerformer(Performer):
    provider_name = 'test'

    def perform(self, command, logger=None, writein=None):
        return command


class BaseTestExecutor:
    """
    Testing basic provider function and inheritance
    """
    @classmethod
    def setup_class(cls):
        cls.test_performer = TestPerformer()


class TestBasic(BaseTestExecutor):

    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.test_executor = Executor(performer=cls.test_performer)

    def test_basic(self):
        command = 'cat /dev/null'
        return_command = self.test_executor.execute(command)
        assert return_command == command

    def test_change_dir(self):
        directory = 'home'
        command = 'cat /dev/null'

        with self.test_executor.change_directory(directory):
            return_command = self.test_executor.execute(command)
        assert return_command == 'cd {directory} && {command}'.format(directory=directory, command=command)

    def test_change_dir_double(self):
        directory = 'home'
        directory2 = 'test'
        command = 'cat /dev/null'

        with self.test_executor.change_directory(directory):
            with self.test_executor.change_directory(directory2):
                return_command = self.test_executor.execute(command)
        assert return_command == 'cd {directory} && cd {directory2} && {command}'.format(directory=directory, directory2=directory2, command=command)

    def test_change_dir_independent(self):
        directory = 'home'
        directory2 = 'test'
        command = 'cat /dev/null'

        with self.test_executor.change_directory(directory):
            self.test_executor.execute(command)

        with self.test_executor.change_directory(directory2):
            return_command = self.test_executor.execute(command)

        assert return_command == 'cd {} && {}'.format(directory2, command)


class TestBasicInheritance(BaseTestExecutor):
    @classmethod
    def setup_class(cls):
        super().setup_class()

        class TestExecutor(Executor):
            def execute(self, command, logger=None, writein=None):
                command = command.wrap('wrap {command} && another')
                return super().execute(command, logger=None, writein=None)

        class TestInheritedExecutor(TestExecutor):
            def execute(self, command, logger=None, writein=None):
                command = command.wrap('wrap2 {command} && another2')
                return super().execute(command, logger=None, writein=None)

        cls.test_executor = TestExecutor(performer=cls.test_performer)
        cls.test_inherited_executor = TestInheritedExecutor(performer=cls.test_performer)

    def test_basic(self):
        command = 'cat /dev/null'
        return_command = self.test_executor.execute(command)
        assert return_command == 'wrap bash -c "{command}" && another'.format(command=command)

    def test_basic_inherited(self):
        command = 'cat /dev/null'
        return_command = self.test_inherited_executor.execute(command)
        assert return_command == 'wrap bash -c "wrap2 bash -c \\"{command}\\" && another2" && another'.format(command=command)

    def test_change_dir(self):
        directory = 'home'
        command = 'cat /dev/null'

        with self.test_executor.change_directory(directory):
            return_command = self.test_executor.execute(command)
        assert return_command == 'wrap bash -c "cd {directory} && {command}" && another'.format(directory=directory, command=command)

    def test_change_dir_inherited(self):
        directory = 'home'
        command = 'cat /dev/null'

        with self.test_inherited_executor.change_directory(directory):
            return_command = self.test_inherited_executor.execute(command)
        assert return_command == 'wrap bash -c "wrap2 bash -c \\"cd {directory} && {command}\\" && another2" && another'.format(directory=directory, command=command)

    def test_change_dir_double(self):
        directory = 'home'
        directory2 = 'test'
        command = 'cat /dev/null'

        with self.test_executor.change_directory(directory):
            with self.test_executor.change_directory(directory2):
                return_command = self.test_executor.execute(command)
        assert return_command == 'wrap bash -c "cd {directory} && cd {directory2} && {command}" && another'.format(directory=directory, directory2=directory2, command=command)

    def test_change_dir_double_inherited(self):
        directory = 'home'
        directory2 = 'test'
        command = 'cat /dev/null'

        with self.test_inherited_executor.change_directory(directory):
            with self.test_inherited_executor.change_directory(directory2):
                return_command = self.test_inherited_executor.execute(command)
        assert return_command == 'wrap bash -c "wrap2 bash -c \\"cd {directory} && cd {directory2} && {command}\\" && another2" && another'.format(directory=directory, directory2=directory2, command=command)

    def test_change_dir_independent(self):
        directory = 'home'
        directory2 = 'test'
        command = 'cat /dev/null'

        with self.test_executor.change_directory(directory):
            self.test_executor.execute(command)

        with self.test_executor.change_directory(directory2):
            return_command = self.test_executor.execute(command)

        assert return_command == 'wrap bash -c "cd {directory2} && {command}" && another'.format(directory2=directory2, command=command)

    def test_change_dir_independent(self):
        directory = 'home'
        directory2 = 'test'
        command = 'cat /dev/null'

        with self.test_inherited_executor.change_directory(directory):
            self.test_inherited_executor.execute(command)

        with self.test_inherited_executor.change_directory(directory2):
            return_command = self.test_inherited_executor.execute(command)

        assert return_command == 'wrap bash -c "wrap2 bash -c \\"cd {directory2} && {command}\\" && another2" && another'.format(directory2=directory2, command=command)


