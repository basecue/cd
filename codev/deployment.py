from .environment import Environment
from .infrastructure import Infrastructure
from .performers import LocalPerformer

from .installation import Installation

import logging
logger = logging.getLogger(__name__)


class Deployment(object):
    def __init__(self, configuration, environment_name, infrastructure_name, installation_name):
        #check
        self.configuration = configuration
        environment_configuration = configuration.environments[environment_name]
        infrastructure_configuration = environment_configuration.infrastructures[infrastructure_name]
        if installation_name not in environment_configuration.installations:
            raise ValueError('Bad installation')

        self._environment = Environment(environment_configuration)
        self._infrastructure = Infrastructure(infrastructure_configuration)
        self._installation = Installation(installation_name, configuration)

        self.isolation_ident = '%s_%s_%s_%s' % (
            configuration.project,
            environment_name,
            infrastructure_name,
            installation_name
        )

    def performer(self):
        return self._environment.performer(self.isolation_ident)

    def isolation(self):
        isolation = self._environment.create_isolation(self.isolation_ident)

        configuration = self._installation.configuration(isolation)

        # install python3 pip
        isolation.execute('apt-get install python3-pip -y --force-yes')

        # install proper version of codev
        if configuration.debug.distfile:
            isolation.send_file(configuration.debug.distfile.format(version=configuration.version), 'codev.tar.gz')
            isolation.execute('pip3 install --upgrade codev.tar.gz')
        else:
            isolation.execute('pip3 install --upgrade codev=={version}'.format(version=configuration.version))

        return isolation

    def machines(self):
        return self._infrastructure.machines(LocalPerformer())

    def provision(self, machines):
        pass
