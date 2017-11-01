from codev.core.settings import BaseSettings, SettingsError
from codev.control.isolation import PrivilegedIsolation


class VirtualenvIsolationSettings(BaseSettings):
    @property
    def python_version(self):
        python_version = self.data.get('python', None)
        if not python_version:
            return 3
        elif python_version == '2' or python_version.startswith('2.'):
            return python_version
        else:
            raise SettingsError('Unsupported python version for virtualenv isolation.')


class DirectoryIsolation(PrivilegedIsolation):

    def _get_base_dir(self):
        return '~/.share/codev/virtualenv/{ident}/'.format(ident=self.ident.as_directory())

    def exists(self):
        # self.check_execute('[ -d {directory} ]'.format(
        #     directory=self._get_base_dir()
        # ))

        return self.inherited_executor.exists_directory(self._get_base_dir())

    def create(self):
        self.inherited_executor(PrivilegedIsolation).execute(
            'mkdir -p {}'.format(self._get_base_dir())
        )

    def execute_command(self, command):
        command = command.change_directory(
            self._get_base_dir()
        )
        super().execute_command(command)


class VirtualenvIsolation(DirectoryIsolation):
    provider_name = 'virtualenv'
    settings_class = VirtualenvIsolationSettings

    def exists(self):
        return self.inherited_executor.exists() and self.inherited_executor.exists_directory('env')

    def create(self):
        self.inherited_executor.create()

        python_version = self.settings.python_version
        self.inherited_executor.execute('virtualenv -p python{python_version} env'.format(
            python_version=python_version
        ))

    def execute_command(self, command):
        command = command.wrap(
            'source env/bin/activate && {command}'
        )
        return super().execute_command(command)
