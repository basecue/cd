from .machines import MachinesProvider


class Infrastructure(object):
    def __init__(self, configuration, performer):
        self.machines = {}

        for machines_name, machines_configuration in configuration.machines.items():
            machines_provider = MachinesProvider(
                machines_configuration.provider,
                machines_name, performer, machines_configuration.specific
            )
            self.machines[machines_name] = machines_provider.machines()
