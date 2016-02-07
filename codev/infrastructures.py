from .machines import LXCMachine, RealMachine
from .configuration import BaseConfiguration
from .provider import BaseProvider


class BaseMachinesProvider(object):
    def __init__(self, machines_name, performer, configuration_data):
        self.machines_name = machines_name
        self.performer = performer
        self.configuration_data = configuration_data


class ConfigurableMachinesProvider(BaseMachinesProvider):
    configuration_class = None

    def __init__(self, *args, **kwargs):
        super(ConfigurableMachinesProvider, self).__init__(*args, **kwargs)
        self.configuration = self.__class__.configuration_class(self.configuration_data)


class LXCMachinesConfiguration(BaseConfiguration):
    @property
    def distribution(self):
        return self.data.get('distribution')

    @property
    def release(self):
        return self.data.get('release')

    @property
    def architecture(self):
        return self.data.get('architecture')

    @property
    def number(self):
        return int(self.data.get('number'))


class LXCMachinesProvider(ConfigurableMachinesProvider):
    configuration_class = LXCMachinesConfiguration

    def machines(self):
        machines = []
        for i in range(1, self.configuration.number + 1):
            ident = '%s_%000d' % (self.machines_name, i)
            machine = LXCMachine(
                self.performer,
                ident,
                self.configuration.distribution,
                self.configuration.release,
                self.configuration.architecture
            )
            machine.create()
            machine.start()
            machines.append(machine)
        return machines


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


class MachinesProvider(BaseProvider):
    provider_class = BaseMachinesProvider


MachinesProvider.register('lxc', LXCMachinesProvider)
MachinesProvider.register('real', RealMachinesProvider)


class Infrastructure(object):
    def __init__(self, performer, infrastructure_configuration):
        self.machines = {}

        for machines_name, machines_configuration in infrastructure_configuration.machines.items():
            machines_provider = MachinesProvider(
                machines_configuration.provider,
                machines_name, performer, machines_configuration.specific
            )
            self.machines[machines_name] = machines_provider.machines()
