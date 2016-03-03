
from .infrastructure import Infrastructure
from .debug import DebugConfiguration
from .logging import logging_config
from .performer import CommandError
from .isolation import IsolationProvider
from .configuration import YAMLConfigurationReader
from colorama import Fore as color

from logging import getLogger

logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')


class Deployment(object):
    """
    Represents deployment of project. It's basic starting point for all commands.
    """
    def __init__(self, configuration, environment_name, infrastructure_name, installation_name, installation_options):
        environment_configuration = configuration.environments[environment_name]
        installation_configuration = environment_configuration.installations[installation_name]

        infrastructure_configuration = environment_configuration.infrastructures[infrastructure_name]
        self._infrastructure = Infrastructure(infrastructure_name, infrastructure_configuration)

        self.isolation_provider = IsolationProvider(
            configuration.project,
            environment_name,
            infrastructure_name,
            environment_configuration.performer,
            environment_configuration.isolation,
            installation_name,
            installation_options,
            installation_configuration
        )

        self.project_name = configuration.project
        self.environment_name, self.infrastructure_name, self.installation_name, self.installation_options = \
            environment_name, infrastructure_name, installation_name, installation_options

    def install(self):
        """
        Create isolation if it does not exist and start installation in isolation.

        :return: True if installation is successfully realized
        :rtype: bool
        """
        logger.info("Starting installation...")
        isolation = self.isolation_provider.enter(create=True, install=True)

        with isolation.get_fo('.codev') as codev_file:
            version = YAMLConfigurationReader().from_yaml(codev_file).version

        # install python3 pip
        isolation.execute('apt-get install python3-pip -y --force-yes')

        # install proper version of codev
        if not DebugConfiguration.configuration.distfile:
            logger.debug("Install codev version '{version}' to isolation.".format(version=version))
            isolation.execute('pip3 install --upgrade codev=={version}'.format(version=version))
        else:
            distfile = DebugConfiguration.configuration.distfile.format(version=version)
            debug_logger.info('Install codev {distfile}'.format(distfile=distfile))
            isolation.send_file(distfile, '/tmp/codev.tar.gz')
            isolation.execute('pip3 install --upgrade /tmp/codev.tar.gz')

        logger.info("Run 'codev {version}' in isolation.".format(version=version))

        if DebugConfiguration.perform_configuration:
            perform_debug = ' '.join(
                (
                    '--debug {key} {value}'.format(key=key, value=value)
                    for key, value in DebugConfiguration.perform_configuration.data.items()
                )
            )
        else:
            perform_debug = ''

        logging_config(control_perform=True)
        try:
            isolation.background_execute('codev install -d {environment_name} {infrastructure_name} {installation_name}:{installation_options} --perform --force {perform_debug}'.format(
                environment_name=self.environment_name,
                infrastructure_name=self.infrastructure_name,
                installation_name=self.installation_name,
                installation_options=self.installation_options,
                perform_debug=perform_debug
            ), logger=command_logger)
        except CommandError as e:
            command_logger.error(e.error)
            logger.error("Installation failed.")
            return False
        else:
            logger.info("Installation has been successfully completed.")
            return True

    def provision(self):
        """
        Run provisions

        :return: True if provision successfully proceeds
        :rtype: bool
        """
        return self._infrastructure.provision()

    def execute(self, command):
        """
        Create isolation if it does not exist and execute command in isolation.


        :param command: Command to execute
        :type command: str
        :return: True if executed command returns 0
        :rtype: bool
        """
        isolation = self.isolation_provider.enter(create=True)

        logging_config(control_perform=True)
        try:
            isolation.background_execute(command, logger=command_logger)
        except CommandError as e:
            logger.error(e)
            return False
        else:
            logger.info('Command finished.')
            return True

    def join(self):
        """
        Stop the running command in isolation

        :return: True if command was running
        :rtype: bool
        """
        logging_config(control_perform=True)
        isolation = self.isolation_provider.enter()
        if isolation.background_join(logger=command_logger):
            logger.info('Command finished.')
            return True
        else:
            logger.error('No running command.')
            return False

    def stop(self):
        """
        Stop the running command in isolation

        :return: True if command was running
        :rtype: bool
        """
        isolation = self.isolation_provider.enter()
        if isolation.background_stop():
            logger.info('Stop signal has been sent.')
            return True
        else:
            logger.error('No running command.')
            return False

    def kill(self):
        """
        Kill the running command in isolation

        :return: True if command was running
        :rtype: bool
        """
        isolation = self.isolation_provider.enter()
        if isolation.background_kill():
            logger.info('Command has been killed.')
            return True
        else:
            logger.error('No running command.')
            return False

    def shell(self):
        """
        Create isolation if it does not exist and invoke 'shell' in isolation.

        :return:
        :rtype: bool
        """
        isolation = self.isolation_provider.enter(create=True)
        logger.info('Entering isolation shell...')

        #support for history
        import readline
        shell_logger = getLogger('shell')
        SEND_FILE_SHELL_COMMAND = 'send'

        while True:
            command = input(
                (color.GREEN +
                 '{project_name} {environment_name} {infrastructure_name} {installation_name}:{installation_options}' +
                 color.RESET + ':' + color.BLUE + '~' + color.RESET + '$ ').format(
                    project_name=self.project_name,
                    environment_name=self.environment_name,
                    infrastructure_name=self.infrastructure_name,
                    installation_name=self.installation_name,
                    installation_options=self.installation_options
                )
            )
            if command in ('exit', 'quit', 'logout'):
                return True
            if command.startswith(SEND_FILE_SHELL_COMMAND):
                try:
                    source, target = command[len(SEND_FILE_SHELL_COMMAND):].split()
                except ValueError:
                    shell_logger.error('Command {command} needs exactly two arguments: <source> and <target>.'.format(
                        command=SEND_FILE_SHELL_COMMAND
                    ))
                else:
                    try:
                        isolation.send_file(source, target)
                    except CommandError as e:
                        shell_logger.error(e.error)
                continue
            try:
                isolation.background_execute(command, logger=shell_logger)
            except CommandError as e:
                shell_logger.error(e.error)

    def run(self, script):
        """
        Create isolation if it does not exist and run script in isolation.

        :param script: Name of the script
        :type param: str
        :return:
        :rtype: bool
        """
        # TODO
        pass

    def destroy(self):
        """
        Destroy the isolation.

        :return: True if isolation is destroyed
        :rtype: bool
        """
        if self.isolation_provider.destroy():
            logger.info('Isolation has been destroyed.')
            return True
        else:
            logger.info('There is no such isolation.')
            return False
