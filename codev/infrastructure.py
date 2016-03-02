from .machines import MachinesProvider
from .provision import Provision
from .performer import Performer
from logging import getLogger

logger = getLogger(__name__)


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

    def _machines_groups(self):
        machines_groups = {}
        for machines_name, machines_configuration in self.configuration.machines.items():
            machines_provider = MachinesProvider(
                machines_configuration.provider,
                machines_name, self.performer, configuration_data=machines_configuration.specific
            )
            machines_groups[machines_name] = machines_provider.create_machines()
        return machines_groups

    def provision(self):
        logger.info('Installing provisioner...')
        self._provision_provider.install()
        logger.info('Creating machines...')
        machines_groups = self._machines_groups()
        logger.info('Starting provisioning...')
        return self._provision_provider.run(machines_groups)
