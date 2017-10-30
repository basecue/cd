from codev.core.executor import Command
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
            raise SettingsError('Unsupported python version for virtualenv isolator.')


class DirectoryIsolation(PrivilegedIsolation):

    def _get_base_dir(self):
        return '~/.share/codev/virtualenv/{ident}/'.format(ident=self.ident.as_directory())

    def exists(self):
        return Command.exists_directory(self._get_base_dir()).check_execute(super())

    def create(self):
        return Command(
            'mkdir -p {}'.format(self._get_base_dir())
        ).execute(super())

    def execute(self, command):
        return command.change_directory(
            self._get_base_dir()
        ).execute(super())


class VirtualenvIsolation(DirectoryIsolation):
    provider_name = 'virtualenv'
    settings_class = VirtualenvIsolationSettings

    def exists(self):
        return super().exists() and Command.exists_directory('env').check_execute(self)

    def create(self):
        super().create()

        python_version = self.settings.python_version
        Command(
            'virtualenv -p python{python_version} env'.format(
                python_version=python_version
            )
        ).execute(super())

    def execute(self, command):
        return command.wrap(
            'source env/bin/activate && {command}'
        ).execute(super())
