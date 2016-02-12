from .machines import MachinesProvider


class Infrastructure(object):
    def __init__(self, configuration):
        self.configuration = configuration

    def machines(self, performer):
        machines = {}
        for machines_name, machines_configuration in self.configuration.machines.items():
            machines_provider = MachinesProvider(
                machines_configuration.provider,
                machines_name, performer, machines_configuration.specific
            )
            machines.setdefault(machines_name, []).append(machines_provider.create_machines())
        return machines
