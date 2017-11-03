from codev.core.machines import BaseMachine


class DirectoryBaseMachine(BaseMachine):

    def _get_base_dir(self):
        return '~/.share/codev/virtualenv/{ident}/'.format(ident=self.ident.as_directory())

    def exists(self):
        return self.inherited_executor.exists_directory(self._get_base_dir())

    def create(self):
        self.inherited_executor().execute(
            'mkdir -p {}'.format(self._get_base_dir())
        )

    def execute_command(self, command):
        command = command.change_directory(
            self._get_base_dir()
        )
        super().execute_command(command)


class VirtualenvBaseMachine(DirectoryBaseMachine):
    def exists(self):
        return self.inherited_executor.exists() and self.inherited_executor.exists_directory('env')

    def create(self):
        self.inherited_executor.create()

        python_version = self.settings.python_version
        self.inherited_executor.execute('virtualenv -p python{python_version} env'.format(
            python_version=python_version
        ))

    def is_started(self):
        return True

    def destroy(self):
        self.inherited_executor.execute('rm -rf env')

    def execute_command(self, command):
        command = command.wrap(
            'source env/bin/activate && {command}'
        )
        return super().execute_command(command)