from codev.configuration import BaseConfiguration
from codev.machines import MachinesProvider, BaseMachinesProvider
from codev.provider import ConfigurableProvider


class RealMachine(object):
    def __init__(self, host):
        self.host = host


class RealMachinesConfiguration(BaseConfiguration):
    @property
    def hosts(self):
        return self.data.get('hosts')


class RealMachinesProvider(BaseMachinesProvider, ConfigurableProvider):
    configuration_class = RealMachinesConfiguration

    def create_machines(self):
        machines = []
        for host in self.configuration.hosts:
            machines.append(RealMachine(host))
        return machines


MachinesProvider.register('real', RealMachinesProvider)