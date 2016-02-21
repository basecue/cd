from .environment import Environment
from .installation import Installation

from .debug import DebugConfiguration
import logging
logger = logging.getLogger(__name__)

from .logging import command_logger


class Deployment(object):
    def __init__(self, configuration, environment_name, infrastructure_name, installation_name):
        environment_configuration = configuration.environments[environment_name]

        if installation_name not in environment_configuration.installations:
            raise ValueError('Bad installation')

        isolation_ident = '%s_%s_%s_%s' % (
            configuration.project,
            environment_name,
            infrastructure_name,
            installation_name
        )

        self._environment = Environment(environment_configuration, infrastructure_name, isolation_ident)

        #TODO configuration = only specific configuration for chosen installation
        self._installation = Installation(installation_name, configuration)

    @property
    def performer(self):
        return self._environment.performer

    def isolation(self):
        logger.info("Switching to isolation...")
        isolation = self._environment.create_isolation()
        return isolation

    def install(self):
        isolation = self.isolation()

        directory, version = self._installation.configure(isolation)

        # install python3 pip
        isolation.execute('apt-get install python3-pip -y --force-yes')

        # install proper version of codev
        if not DebugConfiguration.configuration.distfile:
            isolation.execute('pip3 install --upgrade codev=={version}'.format(version=version))
        else:
            isolation.send_file(DebugConfiguration.configuration.distfile.format(version=version), 'codev.tar.gz')
            isolation.execute('pip3 install --upgrade codev.tar.gz')

        isolation.execute('cd %s' % directory)
        logger.info("Run 'codev {version}' in isolation.".format(version=version))

        command_logger.set_control_perform_command_output()
        isolation.execute('codev install -d {environment} {infrastructure} {installation} --perform -f'.format(
            environment=self.environment_name,
            infrastructure=self.infrastructure_name,
            installation=self.installation,
        ))

    def provision(self):
        self._environment.provision()
