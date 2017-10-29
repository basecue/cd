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


class VirtualenvIsolation(PrivilegedIsolation):
    provider_name = 'virtualenv'
    settings_class = VirtualenvIsolationSettings

    def _get_base_dir(self):
        return '~/.share/codev/virtualenv/{ident}/'.format(ident=self.ident)

    def exists(self):
        with super().change_directory(self._get_base_dir()):
            return super().exists_directory('env')

    def create(self):
        python_version = self.settings.python_version
        with super().change_directory(self._get_base_dir()):
            super().execute(
                'virtualenv -p python{python_version} env'.format(
                    python_version=python_version
                )
            )

    def execute(self, command, logger=None, writein=None):
        command = command.wrap('source env/bin/activate && {command}')
        command.change_directory(self._get_base_dir())
        return super().execute(command, logger=logger, writein=writein)
