from codev.configuration import BaseConfiguration
from codev.machines import ConfigurableMachinesProvider, MachinesProvider


class RealMachine(object):
    def __init__(self, ip):
        self.ip = ip


class RealMachinesConfiguration(BaseConfiguration):
    @property
    def ips(self):
        return self.data.get('ips')


class RealMachinesProvider(ConfigurableMachinesProvider):
    configuration_class = RealMachinesConfiguration

    def machines(self):
        machines = []
        for ip in self.configuration.ips:
            machines.append(RealMachine(ip))
        return machines


MachinesProvider.register('real', RealMachinesProvider)