from .machines import MachinesProvider
from .provision import Provision
from .performer import Performer


class Infrastructure(object):
    def __init__(self, name, configuration):
        self.name = name
        self.configuration = configuration

        self.performer = Performer('local')

        self._provision_provider = Provision(
            configuration.provision.provider,
            self.performer,
            self.name,
            configuration_data=configuration.provision.specific
        )

    def _machines(self):
        machines = {}
        for machines_name, machines_configuration in self.configuration.machines.items():
            machines_provider = MachinesProvider(
                machines_configuration.provider,
                machines_name, self.performer, configuration_data=machines_configuration.specific
            )
            machines.setdefault(machines_name, []).append(machines_provider.create_machines())
        return machines

    def provision(self):
        self._provision_provider.install()
        machines = self._machines()
        self._provision_provider.run(machines)