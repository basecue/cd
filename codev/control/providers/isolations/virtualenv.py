from codev.core.providers.machines import VirtualenvBaseMachine
from codev.core.settings import BaseSettings, SettingsError
from codev.control.isolation import PrivilegedIsolation


class VirtualenvIsolation(VirtualenvBaseMachine, PrivilegedIsolation):
    provider_name = 'virtualenv'

