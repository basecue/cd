from codev.settings import BaseSettings, SettingsError
from codev.isolator import Isolator


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
        self._env_dir = '~/.share/codev/virtualenv/{ident}'.format(ident=self.ident)

    def exists(self):
        return self.performer.check_execute('[ -d {env_dir} ]'.format(env_dir=self._env_dir))

    def create(self):
        python_version = self.settings.python_version
        self.performer.execute('virtualenv -p python{python_version} {env_dir}'.format(
            python_version=python_version, env_dir=self._env_dir)
        )

    def is_started(self):
        return self.exists()

    def destroy(self):
        self.performer.execute('rm -rf {env_dir}'.format(env_dir=self._env_dir))

    def _execute(self, command, logger=None, writein=None, max_lines=None):
        return super().execute(
            'bash -c "source {env_dir}/bin/activate && {command}"'.format(
                env_dir=self._env_dir,
                command=command
            ), logger=None, writein=None, max_lines=None
        )
