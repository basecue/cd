from .configuration import Configuration
from .installation import Installation
from .logging import logging_config
from .performer import CommandError, Performer
from .provision import Provisioner

from colorama import Fore as color, Style as style

from logging import getLogger

logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')


class Deployment(object):
    """
    Deployment of project.
    """
    def __init__(
            self,
            settings,
            environment_name,
            configuration_name,
            installation_name,
            installation_options,
            next_installation_name='',
            next_installation_options='',
            performer_provider=None,
            performer_specific={},
            disable_isolation=False
    ):
        environment_settings = settings.environments[environment_name]
        self.environment = environment_name
        self.project_name = settings.project

        # installation
        try:
            installation_settings = environment_settings.installations[installation_name]
        except KeyError as e:
            raise ValueError(
                "Installation '{installation_name}' is not allowed installation for environment '{environment_name}'.".format(
                    installation_name=installation_name,
                    environment_name=environment_name,
                    project_name=self.project_name
                )
            ) from e
        self.installation = Installation(
            installation_name,
            installation_options,
            settings_data=installation_settings
        )

        # next installation
        if next_installation_name:
            self.next_installation = Installation(
                next_installation_name,
                next_installation_options,
                settings_data=installation_settings
            )
        else:
            self.next_installation = None

        # configuration
        configuration_settings = environment_settings.configurations[configuration_name]
        self.configuration = Configuration(configuration_name, configuration_settings)

        ident = '%s:%s:%s:%s' % (
            settings.project,
            environment_name,
            configuration_name,
            self.installation.ident,
        )
        if self.next_installation:
            ident = '%s:%s' % (ident, self.next_installation.ident)

        # performer
        if not performer_provider:
            performer_settings = environment_settings.performer
            performer_provider = performer_settings.provider
            performer_specific = performer_settings.specific

        performer = Performer(
            performer_provider,
            settings_data=performer_specific
        )

        self.current_installation = self.installation

        if not disable_isolation:
            self.performer = self._isolation = self.configuration.isolation(performer, self.installation, self.next_installation, ident)
            if self.next_installation and self._isolation.exists():
                self.current_installation = self.next_installation
        else:
            self.performer = performer
            self._isolation = None
            self.current_installation = None
            # TODO change
            logging_config(perform=True)

        # provisioner
        provision_settings = configuration_settings.provision
        self.provisioner = Provisioner(
            provision_settings.provider,
            provision_settings.scripts,
            self.performer,
            self.configuration,
            settings_data=provision_settings.specific
        )

    def isolation(self, create=False):
        if self._isolation:
            self.current_installation = self._isolation.enter(create=create)
            return self._isolation
        else:
            logger.error('Isolation is disabled.')
            return False

    def deploy(self):
        with self.performer.change_directory(self.installation.directory):
            return self.provisioner.provision(self.deployment_info())

    def installation_transition(self):
        deployment_info = self.deployment_info(transition=False)

        deployment_info.update(dict(
            color_installation=color.GREEN,
            color_reset=color.RESET + style.RESET_ALL
        ))

        if self.next_installation:
            if not self.current_installation:
                color_installation = color.GREEN
                color_next_installation = color.GREEN
            elif self.current_installation == self.installation:
                color_installation = color.GREEN + style.BRIGHT
                color_next_installation = color.GREEN
            else:
                color_installation = color.GREEN
                color_next_installation = color.GREEN + style.BRIGHT

            color_options = dict(
                color_installation=color_installation,
                color_next_installation=color_next_installation,

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
            project=self.project_name,
            environment=self.environment,
            configuration=self.configuration.name,
            installation=self.installation.name,
            installation_options=self.installation.options,
            next_installation=self.next_installation.name if self.next_installation else '',
            next_installation_options=self.next_installation.options if self.next_installation else '',
            installation_transition=self.installation_transition() if transition else ''
        )

    def install(self):
        """
        Create isolation if it does not exist and start installation in isolation.

        :return: True if installation is successfully realized
        :rtype: bool
        """
        return self._isolation.install(self.environment)

    def run(self, command):
        """
        Run command in project context in isolation.

        :param command: Command to execute
        :type command: str
        :return: True if executed command returns 0
        :rtype: bool
        """
        isolation = self.isolation()

        logging_config(control_perform=True)
        try:
            # TODO refactorize into isolation
            with isolation.change_directory(isolation.installation.directory):
                isolation.run_script(command, arguments=self.deployment_info(), logger=command_logger)
        except CommandError as e:
            logger.error(e)
            return False
        else:
            return True

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
            isolation.execute(command, logger=command_logger)
        except CommandError as e:
            logger.error(e)
            return False
        else:
            logger.info('Command finished.')
            return True
    #
    # def join(self):
    #     """
    #     Stop the running command in isolation
    #
    #     :return: True if command was running
    #     :rtype: bool
    #     """
    #     logging_config(control_perform=True)
    #     isolation = self.isolation()
    #     if isolation.background_join(logger=command_logger):
    #         logger.info('Command finished.')
    #         return True
    #     else:
    #         logger.error('No running command.')
    #         return False
    #
    # def stop(self):
    #     """
    #     Stop the running command in isolation
    #
    #     :return: True if command was running
    #     :rtype: bool
    #     """
    #     isolation = self.isolation()
    #     if isolation.background_stop():
    #         logger.info('Stop signal has been sent.')
    #         return True
    #     else:
    #         logger.error('No running command.')
    #         return False
    #
    # def kill(self):
    #     """
    #     Kill the running command in isolation
    #
    #     :return: True if command was running
    #     :rtype: bool
    #     """
    #     isolation = self.isolation()
    #     if isolation.background_kill():
    #         logger.info('Command has been killed.')
    #         return True
    #     else:
    #         logger.error('No running command.')
    #         return False

    def shell(self):
        """
        Create isolation if it does not exist and invoke 'shell' in isolation.

        :return:
        :rtype: bool
        """
        isolation = self.isolation(create=True)

        logger.info('Entering isolation shell...')

        #support for history
        import readline
        shell_logger = getLogger('shell')
        SEND_FILE_SHELL_COMMAND = 'send'

        while True:

            command = input(
                (color.GREEN +
                 '{project} {environment} {configuration} {installation_transition}' +
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
                isolation.execute(command, logger=shell_logger)
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

    def info(self):
        isolation = self.isolation()

        return dict(
            isolation=isolation,
            machines_groups=self.configuration.machines_groups(isolation),
            connectivity=isolation.connectivity
        )

