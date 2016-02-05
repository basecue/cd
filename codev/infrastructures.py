from .machines import LXCMachine
from .configuration import BaseConfiguration


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


class LXCMachines(object):
    def __new__(cls, machines_name, performer, configuration):
        machines = []
        for i in range(1, configuration.number + 1):
            ident = '%s_%000d' % (machines_name, i)
            machine = LXCMachine(
                performer,
                ident,
                configuration.distribution,
                configuration.release,
                configuration.architecture
            )
            machine.create()
            machine.start()
            machines.append(machine)
        return machines


MACHINE_PROVIDERS_BY_NAME = {
    'lxc': {
        'machines': LXCMachines,
        'configuration': LXCMachinesConfiguration
    }
}


class Machines(object):
    def __new__(cls, machines_name, performer, provider, data):
        defs = MACHINE_PROVIDERS_BY_NAME[provider]
        configuration = defs['configuration'](data)
        return defs['machines'](machines_name, performer, configuration)


class Infrastructure(object):
    def __init__(self, performer, infrastructure_configuration):
        machines_configuration = infrastructure_configuration.machines
        self.machines = {}

        for machines_name, configuration in machines_configuration.items():
            machine_provider = configuration.provider

            self.machines[machines_name] = Machines(machines_name, performer, machine_provider, configuration.specific)
