from .environment import Environment
from .installation import Installation

from .debug import DebugConfiguration
import logging
logger = logging.getLogger(__name__)

from .logging import logging_config
command_logger = logging.getLogger('command')


class Deployment(object):
    def __init__(self, configuration, environment_name, infrastructure_name, installation_name, installation_options):
        environment_configuration = configuration.environments[environment_name]
        installation_configuration = environment_configuration.installations[installation_name]

        isolation_ident = '%s_%s_%s_%s' % (
            configuration.project,
            environment_name,
            infrastructure_name,
            installation_name
        )

        self._environment = Environment(environment_configuration, infrastructure_name, isolation_ident)
        self._installation = Installation(
            installation_name,
            installation_options,
            configuration_data=installation_configuration
        )

        self.project_name = configuration.project
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
        if DebugConfiguration.perform_configuration:
            debug = ' '.join(
                (
                    '--debug {key} {value}'.format(key=key, value=value)
                    for key, value in DebugConfiguration.perform_configuration.data.items()
                )
            )
        else:
            debug = ''

        #TODO change actual directory in codev with some option - cd directory
        isolation.execute('codev install -d {environment_name} {infrastructure_name} {installation_name}:{installation_options} --path {directory} --perform --force {debug}'.format(
            environment_name=self.environment_name,
            infrastructure_name=self.infrastructure_name,
            installation_name=self.installation_name,
            installation_options=self.installation_options,
            directory=directory,
            debug=debug
        ), logger=command_logger)

    def provision(self):
        self._environment.provision()

    @property
    def _performer(self):
        return self._environment.performer

    def join(self):
        logging_config(control_perform=True)
        if self._performer.join():
            logger.info('Command finished.')
        else:
            logger.info('No running command.')

    def stop(self):
        if self._performer.stop():
            logger.info('Stop signal has been sent.')
        else:
            logger.info('No running command.')

    def kill(self):
        if self._performer.kill():
            logger.info('Command killed.')
        else:
            logger.info('No running command.')

    def execute(self, command):
        isolation = self.isolation()

        logging_config(control_perform=True)
        isolation.execute(command)
        logger.info('Command finished.')

    def run(self, script):
        pass
