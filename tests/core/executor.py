from codev.core.executor import BareExecutor, ProxyExecutor


class TestExecutor(BareExecutor):

    def execute_command(self, command):
        return str(command)


class BaseTestExecutor:
    """
    Testing basic provider function and inheritance
    """
    @classmethod
    def setup_class(cls):
        cls.test_executor = TestExecutor()


class TestBasic(BaseTestExecutor):

    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.test_proxy_executor = ProxyExecutor(executor=cls.test_executor)

    def test_basic(self):
        command = 'cat /dev/null'
        return_command = self.test_proxy_executor.execute(command)
        assert return_command == command

    def test_change_dir(self):
        directory = 'home'
        command = 'cat /dev/null'

        with self.test_proxy_executor.change_directory(directory):
            return_command = self.test_proxy_executor.execute(command)
        assert return_command == 'cd {directory} && {command}'.format(directory=directory, command=command)

    def test_change_dir_double(self):
        directory = 'home'
        directory2 = 'test'
        command = 'cat /dev/null'

        with self.test_proxy_executor.change_directory(directory):
            with self.test_proxy_executor.change_directory(directory2):
                return_command = self.test_proxy_executor.execute(command)
        assert return_command == 'cd {directory} && cd {directory2} && {command}'.format(directory=directory, directory2=directory2, command=command)

    def test_change_dir_independent(self):
        directory = 'home'
        directory2 = 'test'
        command = 'cat /dev/null'

        with self.test_proxy_executor.change_directory(directory):
            self.test_proxy_executor.execute(command)

        with self.test_proxy_executor.change_directory(directory2):
            return_command = self.test_proxy_executor.execute(command)

        assert return_command == 'cd {} && {}'.format(directory2, command)


class TestBasicInheritance(BaseTestExecutor):
    @classmethod
    def setup_class(cls):
        super().setup_class()

        class TestProxyExecutor(ProxyExecutor):
            def execute_command(self, command):
                command = command.wrap('wrap {command} && another')
                return super().execute_command(command)

        class TestInheritedProxyExecutor(ProxyExecutor):
            executor_class = TestProxyExecutor

            def execute_command(self, command, logger=None, writein=None):
                command = command.wrap('wrap2 {command} && another2')
                return super().execute_command(command)

        cls.test_proxy_executor = TestProxyExecutor(executor=cls.test_executor)
        cls.test_inherited_proxy_executor = TestInheritedProxyExecutor(executor=cls.test_executor)

    def test_basic(self):
        command = 'cat /dev/null'
        return_command = self.test_proxy_executor.execute(command)
        assert return_command == 'wrap bash -c "{command}" && another'.format(command=command)

    def test_basic_inherited(self):
        command = 'cat /dev/null'
        return_command = self.test_inherited_proxy_executor.execute(command)
        assert return_command == 'wrap bash -c "wrap2 bash -c \\"{command}\\" && another2" && another'.format(command=command)

    def test_change_dir(self):
        directory = 'home'
        command = 'cat /dev/null'

        with self.test_proxy_executor.change_directory(directory):
            return_command = self.test_proxy_executor.execute(command)
        assert return_command == 'wrap bash -c "cd {directory} && {command}" && another'.format(directory=directory, command=command)

    def test_change_dir_inherited(self):
        directory = 'home'
        command = 'cat /dev/null'

        with self.test_inherited_proxy_executor.change_directory(directory):
            return_command = self.test_inherited_proxy_executor.execute(command)
        assert return_command == 'wrap bash -c "wrap2 bash -c \\"cd {directory} && {command}\\" && another2" && another'.format(directory=directory, command=command)

    def test_change_dir_double(self):
        directory = 'home'
        directory2 = 'test'
        command = 'cat /dev/null'

        with self.test_proxy_executor.change_directory(directory):
            with self.test_proxy_executor.change_directory(directory2):
                return_command = self.test_proxy_executor.execute(command)
        assert return_command == 'wrap bash -c "cd {directory} && cd {directory2} && {command}" && another'.format(directory=directory, directory2=directory2, command=command)

    def test_change_dir_double_inherited(self):
        directory = 'home'
        directory2 = 'test'
        command = 'cat /dev/null'

        with self.test_inherited_proxy_executor.change_directory(directory):
            with self.test_inherited_proxy_executor.change_directory(directory2):
                return_command = self.test_inherited_proxy_executor.execute(command)
        assert return_command == 'wrap bash -c "wrap2 bash -c \\"cd {directory} && cd {directory2} && {command}\\" && another2" && another'.format(directory=directory, directory2=directory2, command=command)

    def test_change_dir_independent(self):
        directory = 'home'
        directory2 = 'test'
        command = 'cat /dev/null'

        with self.test_proxy_executor.change_directory(directory):
            self.test_executor.execute(command)

        with self.test_proxy_executor.change_directory(directory2):
            return_command = self.test_executor.execute(command)

        assert return_command == 'wrap bash -c "cd {directory2} && {command}" && another'.format(directory2=directory2, command=command)

    def test_change_dir_independent(self):
        directory = 'home'
        directory2 = 'test'
        command = 'cat /dev/null'

        with self.test_inherited_proxy_executor.change_directory(directory):
            self.test_inherited_proxy_executor.execute(command)

        with self.test_inherited_proxy_executor.change_directory(directory2):
            return_command = self.test_inherited_proxy_executor.execute(command)

        assert return_command == 'wrap bash -c "wrap2 bash -c \\"cd {directory2} && {command}\\" && another2" && another'.format(directory2=directory2, command=command)


class TestAdvancedInheritance(BaseTestExecutor):
    @classmethod
    def setup_class(cls):
        super().setup_class()

        class TestProxyExecutor(ProxyExecutor):

            def execute_command(self, command):
                command = command.wrap('wrap {command} && another')
                return super().execute_command(command)

        class TestInheritedProxyExecutor(ProxyExecutor):
            executor_class = TestProxyExecutor

            def execute_command(self, command, logger=None, writein=None):
                command = command.wrap('wrap2 {command} && another2')
                return super().execute_command(command)

        class TestSecondInheritedProxyExecutor(ProxyExecutor):
            executor_class = TestInheritedProxyExecutor


        cls.test_proxy_executor = TestProxyExecutor(executor=cls.test_executor)
        cls.test_inherited_proxy_executor = TestSecondInheritedProxyExecutor(executor=cls.test_executor)