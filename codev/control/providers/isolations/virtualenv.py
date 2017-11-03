from codev.core.providers.machines import VirtualenvBaseMachine
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


class VirtualenvIsolation(VirtualenvBaseMachine, PrivilegedIsolation):
    provider_name = 'virtualenv'
    settings_class = VirtualenvIsolationSettings
