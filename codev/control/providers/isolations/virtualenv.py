from codev.core.providers.machines import VirtualenvBaseMachine
from codev.control.isolation import PrivilegedIsolation


class VirtualenvIsolation(VirtualenvBaseMachine, PrivilegedIsolation):
    provider_name = 'virtualenv'
