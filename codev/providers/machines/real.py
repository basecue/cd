from codev.settings import BaseSettings
from codev.machines import MachinesProvider, BaseMachine


class RealMachine(BaseMachine):
    def __init__(self, host):
        self.host = host


class RealMachinesSettings(BaseSettings):
    @property
    def hosts(self):
        return self.data.get('hosts')


class RealMachinesProvider(MachinesProvider):
    provider_name = 'real'
    settings_class = RealMachinesSettings

    def machines(self, create=False, pub_key=None):
        machines = []
        for host in self.settings.hosts:
            machines.append(RealMachine(host))
        return machines
