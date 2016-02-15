from codev.configuration import BaseConfiguration
from codev.machines import MachinesProvider, BaseMachinesProvider
from codev.provider import ConfigurableProvider


class RealMachine(object):
    def __init__(self, ip):
        self.ip = ip


class RealMachinesConfiguration(BaseConfiguration):
    @property
    def ips(self):
        return self.data.get('ips')


class RealMachinesProvider(BaseMachinesProvider, ConfigurableProvider):
    configuration_class = RealMachinesConfiguration

    def create_machines(self):
        machines = []
        for ip in self.configuration.ips:
            machines.append(RealMachine(ip))
        return machines


MachinesProvider.register('real', RealMachinesProvider)