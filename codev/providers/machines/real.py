from codev.configuration import BaseConfiguration
from codev.machines import MachinesProvider, BaseMachinesProvider, BaseMachine


class RealMachine(BaseMachine):
    def __init__(self, host):
        self.host = host


class RealMachinesConfiguration(BaseConfiguration):
    @property
    def hosts(self):
        return self.data.get('hosts')


class RealMachinesProvider(BaseMachinesProvider):
    configuration_class = RealMachinesConfiguration

    def machines(self, create=False, pub_key=None):
        machines = []
        for host in self.configuration.hosts:
            machines.append(RealMachine(host))
        return machines


MachinesProvider.register('real', RealMachinesProvider)