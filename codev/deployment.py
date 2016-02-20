from .environment import Environment
from .installation import Installation

from . import debug
import logging
logger = logging.getLogger(__name__)


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
        isolation = self._environment.create_isolation()
        return isolation

    def install(self):
        isolation = self.isolation()

        directory, version = self._installation.install(isolation)

        # install python3 pip
        isolation.execute('apt-get install python3-pip -y --force-yes')

        # install proper version of codev
        if not debug.distfile:
            isolation.execute('pip3 install --upgrade codev=={version}'.format(version=version))
        else:
            isolation.send_file(debug.distfile.format(version=version), 'codev.tar.gz')
            isolation.execute('pip3 install --upgrade codev.tar.gz')

        isolation.execute('cd %s' % directory)

        isolation.execute('codev install -d {environment} {infrastructure} {installation} --perform -f'.format(
            environment=self.environment_name,
            infrastructure=self.infrastructure_name,
            installation=self.installation,
        ))

    def provision(self):
        self._environment.provision()
