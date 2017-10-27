from codev.core.settings import BaseSettings, SettingsError
from codev.control.isolator import Isolator, PrivilegedIsolation


class VirtualenvIsolatorSettings(BaseSettings):
    @property
    def python_version(self):
        python_version = self.data.get('python', None)
        if not python_version:
            return 3
        elif python_version == '2' or python_version.startswith('2.'):
            return python_version
        else:
            raise SettingsError('Unsupported python version for virtualenv isolator.')


class VirtualenvIsolator(Isolator):
    provider_name = 'virtualenv'
    settings_class = VirtualenvIsolatorSettings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_dir = '~/.share/codev/virtualenv/{ident}/'

    def get(self, ident):
        return VirtualenvIsolation(base_dir=self.base_dir)

    def create(self, ident):
        python_version = self.settings.python_version
        self.performer.execute(
            'virtualenv -p python{python_version} env'.format(
                python_version=python_version
            )
        )
        return self.get(ident)


class VirtualenvIsolation(PrivilegedIsolation):
    def execute(self, command, logger=None, writein=None):
        command = 'source env/bin/activate && {command}'.format(
            env_dir=self._env_dir,
            command=command
        )
        return self.performer.execute_wrapper(
            '{command}', command, logger=logger, writein=writein
        )

