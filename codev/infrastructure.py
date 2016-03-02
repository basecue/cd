from .machines import MachinesProvider
from .provision import Provision
from .performer import Performer, CommandError
from logging import getLogger

logger = getLogger(__name__)


class Infrastructure(object):
    def __init__(self, name, configuration):
        self.name = name
        self.configuration = configuration

        self.performer = Performer('local')
        self.scripts = configuration.provision.scripts

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
        self.performer.run_scripts(self.scripts.onstart)
        try:
            logger.info('Installing provisioner...')
            self._provision_provider.install()

            logger.info('Creating machines...')
            machines_groups = self._machines_groups()

            logger.info('Starting provisioning...')
            self._provision_provider.run(machines_groups)
        except CommandError as e:
            logger.error(e)
            self.performer.run_scripts(
                self.scripts.onerror,
                dict(
                    command=e.command,
                    exit_code=e.exit_code,
                    error=e.error
                )
            )
            return False
        else:
            self.performer.run_scripts(self.scripts.onsuccess)
            return True
