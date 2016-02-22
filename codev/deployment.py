from .environment import Environment
from .installation import Installation

from .debug import DebugConfiguration
import logging
logger = logging.getLogger(__name__)

from .logging import logging_config


class Deployment(object):
    def __init__(self, configuration, environment_name, infrastructure_name, installation_name, installation_options):
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
        self._installation = Installation(installation_name, installation_options)

        self.environment_name, self.infrastructure_name, self.installation_name, self.installation_options = \
            environment_name, infrastructure_name, installation_name, installation_options

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

        logger.info("Run 'codev {version}' in isolation.".format(version=version))

        logging_config(control_perform=True)
        #TODO change actual directory in codev with some option - cd directory
        # logger = logging.getLogger('command')
        # logger.info('test')
        isolation.execute('pwd')
        isolation.execute('codev install -d {environment_name} {infrastructure_name} {installation_name}:{installation_options} --perform -f'.format(
            environment_name=self.environment_name,
            infrastructure_name=self.infrastructure_name,
            installation_name=self.installation_name,
            installation_options=self.installation_options
        ))

    def provision(self):
        self._environment.provision()

    @property
    def _performer(self):
        return self._environment.performer

    def join(self):
        logging_config(control_perform=True)
        self._performer.join()

    def stop(self):
        logging_config(control_perform=True)
        self._performer.stop()

    def kill(self):
        logging_config(control_perform=True)
        self._performer.kill()

    def execute(self, command):
        isolation = self.isolation()

        logging_config(control_perform=True)
        isolation.execute(command)

    def run(self, script):
        pass