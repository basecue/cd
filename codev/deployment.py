from .configuration import Configuration
from .source import Source
from .logging import logging_config
from .performer import CommandError, Performer
from .isolator import Isolator

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
            disable_isolation=False
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
        source = Source(
            source_name,
            source_options,
            settings_data=source_settings
        )

        # next source
        if next_source_name:
            next_source = Source(
                next_source_name,
                next_source_options,
                settings_data=source_settings
            )
        else:
            next_source = None

        # TODO add codev version?
        ident = '{project}:{environment}:{configuration}:{source_ident}:{next_source_ident}'.format(
            project=settings.project,
            environment=environment_name,
            configuration=configuration_name,
            source_ident=source.ident,
            next_source_ident=next_source.ident if next_source else ''
        )

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
        if not disable_isolation:
            isolator_settings = environment_settings.isolator
            isolator_provider = isolator_settings.provider
            isolator_specific = isolator_settings.specific

            self.performer = Isolator(isolator_provider, performer, settings_data=isolator_specific, ident=ident)
        else:
            logging_config(perform=True)
            self.performer = performer

        # configuration
        configuration_settings = environment_settings.configurations[configuration_name]
        self.configuration = Configuration(
            self.performer,
            settings.project, environment_name, configuration_name,
            configuration_settings, source, next_source, disable_isolation
        )

    def deploy(self):
        return self.configuration.deploy(self.info)

    def install(self):
        """
        Create isolation if it does not exist and start installation in isolation.

        :return: True if installation is successfully realized
        :rtype: bool
        """
        return self.configuration.install(self.info)

    def run(self, script, arguments=None):
        """
        Run command in project context in isolation.

        :param command: Command to execute
        :type command: str
        :return: True if executed command returns 0
        :rtype: bool
        """

        logging_config(control_perform=True)
        try:
            self.configuration.run_script(script, arguments)
        except CommandError as e:
            logger.error(e)
            return False
        else:
            return True

    def destroy(self):
        """
        Destroy the isolation.

        :return: True if isolation is destroyed
        :rtype: bool
        """
        return self.configuration.destroy_isolation()

    @property
    def info(self):
        return dict(
            project=self.project_name,
            environment=self.environment,
            configuration=self.configuration.name,
        )

    @property
    def deployment_info(self):
        return self.configuration.deployment_info(self.info)

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


    # def info(self):
    #     isolation = self.isolation()
    #
    #     return dict(
    #         isolation=isolation,
    #         machines_groups=self.configuration.infrastructure(),
    #         connectivity=isolation.connectivity
    #     )

