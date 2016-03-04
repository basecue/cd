from .infrastructure import Infrastructure
from .installation import Installation
from .debug import DebugConfiguration
from .logging import logging_config
from .performer import CommandError, Performer
from .isolation import Isolation
from hashlib import md5
from .configuration import YAMLConfigurationReader
from colorama import Fore as color, Style as style

from logging import getLogger

logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')


class Deployment(object):
    """
    Represents deployment of project. It's basic starting point for all commands.
    """
    def __init__(
            self,
            configuration,
            environment_name,
            infrastructure_name,
            installation_name,
            installation_options,
            next_installation_name='',
            next_installation_options='',
            perform=False
    ):
        environment_configuration = configuration.environments[environment_name]
        self.environment = environment_name
        self.configuration = configuration


        # performer and infrastructure
        # performer
        if not perform:
            performer_configuration = environment_configuration.performer
            performer_provider = performer_configuration.provider
            performer_specific = performer_configuration.specific
        else:
            performer_provider = 'local'
            performer_specific = {}

        performer = Performer(
            performer_provider,
            configuration_data=performer_specific
        )

        # infrastructure
        infrastructure_configuration = environment_configuration.infrastructures[infrastructure_name]
        self._infrastructure = Infrastructure(performer, infrastructure_name, infrastructure_configuration)

        # installation and isolation

        # installation
        installation_configuration = environment_configuration.installations[installation_name]
        self.installation = Installation(
            installation_name,
            installation_options,
            configuration_data=installation_configuration
        )

        if not perform:
            # next installation
            if next_installation_name:
                self.next_installation = Installation(
                    next_installation_name,
                    next_installation_options,
                    configuration_data=installation_configuration
                )
            else:
                self.next_installation = None

            # isolation
            isolation_configuration = environment_configuration.isolation

            ident = '%s:%s:%s:%s' % (
                configuration.project,
                environment_name,
                infrastructure_name,
                self.installation.ident,
            )

            if self.next_installation:
                ident = '%s:%s' % (ident, self.next_installation.ident)

            self._isolation = Isolation(
                isolation_configuration.provider,
                performer,
                ident=md5(ident.encode()).hexdigest()
            )

            if self._isolation.exists():
                self.current_installation = self.next_installation or self.installation
            else:
                self.current_installation = self.installation

            self.isolation_scripts = isolation_configuration.scripts
        else:
            self.current_installation = self.installation
            self.next_installation = None

    def installation_transition(self):
        deployment_info = self.deployment_info(transition=False)

        if self.next_installation:
            if self.current_installation == self.installation:
                color_installation = color.GREEN + style.BRIGHT
                color_next_installation = color.GREEN
            else:
                color_installation = color.GREEN
                color_next_installation = color.GREEN + style.BRIGHT

            color_options = dict(
                color_installation=color_installation,
                color_next_installation=color_next_installation,
                color_reset=color.RESET + style.RESET_ALL
            )

            deployment_info.update(color_options)
            transition = ' -> {color_next_installation}{next_installation}:{next_installation_options}{color_reset}'.format(
                **deployment_info
            )
        else:
            transition = ''

        return '{color_installation}{installation}:{installation_options}{color_reset}{transition}'.format(
            transition=transition,
            **deployment_info
        )

    def deployment_info(self, transition=True):
        return dict(
            project=self.configuration.project,
            environment=self.environment,
            infrastructure=self._infrastructure.name,
            installation=self.installation.name,
            installation_options=self.installation.options,
            next_installation=self.next_installation.name if self.next_installation else '',
            next_installation_options=self.next_installation.options if self.next_installation else '',
            installation_transition=self.installation_transition() if transition else ''
        )

    def isolation(self, create=False, next_install=False):
        if create:
            logger.info("Creating isolation...")
            if self._isolation.create():
                logger.info("Install project to isolation.")
                self.current_installation = self.installation
                self.current_installation.install(self._isolation)

                # run oncreate scripts
                with self._isolation.change_directory(self.current_installation.directory):
                    self._isolation.run_scripts(self.isolation_scripts.oncreate)
            else:
                if next_install and self.next_installation:
                    logger.info("Transition installation in isolation.")
                    self.current_installation = self.next_installation
                    self.current_installation.install(self._isolation)

        logger.info("Entering isolation...")
        # run onenter scripts
        with self._isolation.change_directory(self.current_installation.directory):
            self._isolation.run_scripts(self.isolation_scripts.onenter)

        return self._isolation

    def install(self):
        """
        Create isolation if it does not exist and start installation in isolation.

        :return: True if installation is successfully realized
        :rtype: bool
        """
        logger.info("Starting installation...")
        isolation = self.isolation(create=True, next_install=True)

        with isolation.change_directory(self.current_installation.directory):
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
            deployment_options = '-e {environment} -i {infrastructure} -s {current_installation.provider_name}:{current_installation.options}'.format(
                current_installation=self.current_installation,
                **self.deployment_info()
            )
            with isolation.change_directory(self.current_installation.directory):
                isolation.background_execute('codev install {deployment_options} --perform --force {perform_debug}'.format(
                    deployment_options=deployment_options,
                    perform_debug=perform_debug
                ), logger=command_logger)
        except CommandError as e:
            command_logger.error(e.error)
            logger.error("Installation failed.")
            return False
        else:
            logger.info("Setting up connectivity.")
            self._infrastructure.connect(isolation)
            logger.info("Installation has been successfully completed.")
            return True

    def provision(self):
        """
        Run provisions

        :return: True if provision successfully proceeds
        :rtype: bool
        """
        return self._infrastructure.provision(self.current_installation)

    def execute(self, command):
        """
        Create isolation if it does not exist and execute command in isolation.


        :param command: Command to execute
        :type command: str
        :return: True if executed command returns 0
        :rtype: bool
        """
        isolation = self.isolation(create=True)

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
        isolation = self.isolation()
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
        isolation = self.isolation()
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
        isolation = self.isolation()
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
        isolation = self.isolation(create=True)
        self._infrastructure.connect(isolation)
        logger.info('Entering isolation shell...')

        #support for history
        import readline
        shell_logger = getLogger('shell')
        SEND_FILE_SHELL_COMMAND = 'send'

        while True:

            command = input(
                (color.GREEN +
                 '{project} {environment} {infrastructure} {installation_transition}' +
                 color.RESET + ':' + color.BLUE + '~' + color.RESET + '$ ').format(
                    **self.deployment_info()
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

    def destroy(self):
        """
        Destroy the isolation.

        :return: True if isolation is destroyed
        :rtype: bool
        """
        if self._isolation.destroy():
            logger.info('Isolation has been destroyed.')
            return True
        else:
            logger.info('There is no such isolation.')
            return False
