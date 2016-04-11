from .configuration import Configuration
from .source import Source
from .logging import logging_config
from .performer import CommandError, Performer
from .provision import Provisioner
from .isolator import Isolator

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
            source_name,
            source_options,
            next_source_name='',
            next_source_options='',
            performer_provider=None,
            performer_specific={},
            isolator_provider='',
            isolator_specific={},
    ):
        environment_settings = settings.environments[environment_name]
        self.environment = environment_name
        self.project_name = settings.project

        # installation
        try:
            source_settings = environment_settings.sources[source_name]
        except KeyError as e:
            raise ValueError(
                "Source '{source_name}' is not allowed source for environment '{environment_name}'.".format(
                    source_name=source_name,
                    environment_name=environment_name,
                    project_name=self.project_name
                )
            ) from e
        self.source = Source(
            source_name,
            source_options,
            settings_data=source_settings
        )

        # next source
        if next_source_name:
            self.next_source = Source(
                next_source_name,
                next_source_options,
                settings_data=source_settings
            )
        else:
            self.next_source = None

        ident = '%s:%s:%s:%s' % (
            settings.project,
            environment_name,
            configuration_name,
            self.source.ident,
        )
        if self.next_source:
            ident = '%s:%s' % (ident, self.next_source.ident)

        # performer
        if not performer_provider:
            performer_settings = environment_settings.performer
            performer_provider = performer_settings.provider
            performer_specific = performer_settings.specific

        performer = Performer(
            performer_provider,
            settings_data=performer_specific
        )

        # isolator
        if not isolator_provider:
            isolator_settings = environment_settings.isolator
            isolator_provider = isolator_settings.provider
            isolator_specific = isolator_settings.specific

        # TODO move to LXC isolator
        from hashlib import md5
        ident = md5(ident.encode()).hexdigest()
        #########

        self.isolator = Isolator(isolator_provider, performer, settings_data=isolator_specific, ident=ident)

        # configuration
        configuration_settings = environment_settings.configurations[configuration_name]
        self.configuration = Configuration(self.isolator, configuration_name, configuration_settings, self.source, self.next_source)

        self.current_source = self.source

        if self.next_source and self.isolator.exists():
            self.current_source = self.next_source
        # if performer == self.performer:
        #     self.current_source = None
        #     logging_config(perform=True)

        # provisioner
        # provision_settings = configuration_settings.provision
        # self.provisioner = Provisioner(
        #     provision_settings.provider,
        #     provision_settings.scripts,
        #     self.isolator,
        #     self.configuration,
        #     settings_data=provision_settings.specific
        # )

    # def isolation(self, create=False):
    #     if self._isolation:
    #         self.current_source = self.isolator.enter(create=create)
    #         return self._isolation
    #     else:
    #         logger.error('Isolation is disabled.')
    #         return False

    def deploy(self):
        return self.configuration.deploy(self.deployment_info())

    def source_transition(self):
        deployment_info = self.deployment_info(transition=False)

        deployment_info.update(dict(
            color_source=color.GREEN,
            color_reset=color.RESET + style.RESET_ALL
        ))

        if self.next_source:
            if not self.current_source:
                color_source = color.GREEN
                color_next_source = color.GREEN
            elif self.current_source == self.source:
                color_source = color.GREEN + style.BRIGHT
                color_next_source = color.GREEN
            else:
                color_source = color.GREEN
                color_next_source = color.GREEN + style.BRIGHT

            color_options = dict(
                color_source=color_source,
                color_next_source=color_next_source,

            )

            deployment_info.update(color_options)
            transition = ' -> {color_next_source}{next_source}:{next_source_options}{color_reset}'.format(
                **deployment_info
            )
        else:
            transition = ''

        return '{color_source}{source}:{source_options}{color_reset}{transition}'.format(
            transition=transition,
            **deployment_info
        )

    def deployment_info(self, transition=True):
        return dict(
            project=self.project_name,
            environment=self.environment,
            configuration=self.configuration.name,
            source=self.source.name,
            source_options=self.source.options,
            next_source=self.next_source.name if self.next_source else '',
            next_source_options=self.next_source.options if self.next_source else '',
            source_transition=self.source_transition() if transition else ''
        )

    def install(self):
        """
        Create isolation if it does not exist and start installation in isolation.

        :return: True if installation is successfully realized
        :rtype: bool
        """
        return self.configuration.install(self.environment)

    def run(self, command):
        """
        Run command in project context in isolation.

        :param command: Command to execute
        :type command: str
        :return: True if executed command returns 0
        :rtype: bool
        """

        logging_config(control_perform=True)
        try:
            with self.isolator.change_directory(self.current_source.directory):
                self.isolator.run_script(command, arguments=self.deployment_info(), logger=command_logger)
        except CommandError as e:
            logger.error(e)
            return False
        else:
            return True

    # def execute(self, command):
    #     """
    #     Create isolation if it does not exist and execute command in isolation.
    #
    #
    #     :param command: Command to execute
    #     :type command: str
    #     :return: True if executed command returns 0
    #     :rtype: bool
    #     """
    #     isolation = self.isolation(create=True)
    #
    #     logging_config(control_perform=True)
    #     try:
    #         isolation.execute(command, logger=command_logger)
    #     except CommandError as e:
    #         logger.error(e)
    #         return False
    #     else:
    #         logger.info('Command finished.')
    #         return True
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

    # def shell(self):
    #     """
    #     Create isolation if it does not exist and invoke 'shell' in isolation.
    #
    #     :return:
    #     :rtype: bool
    #     """
    #     isolation = self.isolation(create=True)
    #
    #     logger.info('Entering isolation shell...')
    #
    #     #support for history
    #     import readline
    #     shell_logger = getLogger('shell')
    #     SEND_FILE_SHELL_COMMAND = 'send'
    #
    #     while True:
    #
    #         command = input(
    #             (color.GREEN +
    #              '{project} {environment} {configuration} {source_transition}' +
    #              color.RESET + ':' + color.BLUE + '~' + color.RESET + '$ ').format(
    #                 **self.deployment_info()
    #             )
    #         )
    #         if command in ('exit', 'quit', 'logout'):
    #             return True
    #         if command.startswith(SEND_FILE_SHELL_COMMAND):
    #             try:
    #                 source, target = command[len(SEND_FILE_SHELL_COMMAND):].split()
    #             except ValueError:
    #                 shell_logger.error('Command {command} needs exactly two arguments: <source> and <target>.'.format(
    #                     command=SEND_FILE_SHELL_COMMAND
    #                 ))
    #             else:
    #                 try:
    #                     isolation.send_file(source, target)
    #                 except CommandError as e:
    #                     shell_logger.error(e.error)
    #             continue
    #         try:
    #             isolation.execute(command, logger=shell_logger)
    #         except CommandError as e:
    #             shell_logger.error(e.error)

    def destroy(self):
        """
        Destroy the isolation.

        :return: True if isolation is destroyed
        :rtype: bool
        """
        if self.isolator.destroy():
            logger.info('Isolation has been destroyed.')
            return True
        else:
            logger.info('There is no such isolation.')
            return False

    # def info(self):
    #     isolation = self.isolation()
    #
    #     return dict(
    #         isolation=isolation,
    #         machines_groups=self.configuration.infrastructure(),
    #         connectivity=isolation.connectivity
    #     )

