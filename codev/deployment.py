from .environment import Environment
from .installation import Installation
from .debug import DebugConfiguration
from .logging import logging_config
from .performer import CommandError

from logging import getLogger

logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')


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

    def _isolation(self):
        logger.info("Switching to isolation...")
        isolation = self._environment.create_isolation()
        return isolation

    def install(self):
        logger.info("Starting installation...")
        isolation = self._isolation()

        directory, version = self._installation.configure(isolation)

        # install python3 pip
        isolation.execute('apt-get install python3-pip -y --force-yes')

        # install proper version of codev
        if not DebugConfiguration.configuration.distfile:
            isolation.execute('pip3 install --upgrade codev=={version}'.format(version=version))
        else:
            distfile = DebugConfiguration.configuration.distfile.format(version=version)
            debug_logger.info('Install codev {distfile}'.format(distfile=distfile))
            isolation.send_file(distfile, 'codev.tar.gz')
            isolation.execute('pip3 install --upgrade codev.tar.gz')

        logger.info("Run 'codev {version}' in isolation.".format(version=version))

        logging_config(control_perform=True)
        if DebugConfiguration.perform_configuration:
            perform_debug = ' '.join(
                (
                    '--debug {key} {value}'.format(key=key, value=value)
                    for key, value in DebugConfiguration.perform_configuration.data.items()
                )
            )
        else:
            perform_debug = ''

        try:
            isolation.execute('codev install -d {environment_name} {infrastructure_name} {installation_name}:{installation_options} --path {directory} --perform --force {perform_debug}'.format(
                environment_name=self.environment_name,
                infrastructure_name=self.infrastructure_name,
                installation_name=self.installation_name,
                installation_options=self.installation_options,
                directory=directory,
                perform_debug=perform_debug
            ), logger=command_logger)
        except CommandError as e:
            logger.error("Installation failed.")
            return False
        else:
            logger.info("Installation has been successfully completed.")
            return True

    def provision(self):
        try:
            self._environment.provision()
        except CommandError as e:
            logger.error(e)
            return False

    @property
    def _performer(self):
        return self._environment.performer

    def join(self):
        logging_config(control_perform=True)
        if self._performer.join():
            logger.info('Command finished.')
            return True
        else:
            logger.error('No running command.')
            return False

    def stop(self):
        if self._performer.stop():
            logger.info('Stop signal has been sent.')
            return True
        else:
            logger.error('No running command.')
            return False

    def kill(self):
        if self._performer.kill():
            logger.info('Command killed.')
            return True
        else:
            logger.error('No running command.')
            return False

    def execute(self, command):
        isolation = self._isolation()

        logging_config(control_perform=True)
        try:
            isolation.execute(command)
        except CommandError as e:
            logger.error(e)
            return False
        else:
            logger.info('Command finished.')
            return True

    def run(self, script):
        pass
