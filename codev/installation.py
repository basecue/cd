from .configuration import Configuration
from .source import Source
from .logging import logging_config
from .performer import CommandError, Performer
from .isolator import Isolator

from logging import getLogger

logger = getLogger(__name__)
command_logger = getLogger('command')


class Installation(object):
    """
    Installation of project.
    """
    def __init__(
            self,
            settings,
            environment_name,
            configuration_name='',
            source_name='',
            source_options='',
            next_source_name='',
            next_source_options='',
            performer_provider=None,
            performer_settings_data=None,
            disable_isolation=False
    ):
        """

        :param settings:
        :type settings: Settings
        :param environment_name:
        :type environment_name: string
        :param configuration_name:
        :type configuration_name: string
        :param source_name:
        :type source_name: string
        :param source_options:
        :type source_options: string
        :param next_source_name:
        :type next_source_name: string
        :param next_source_options:
        :type next_source_options: string
        :param performer_provider:
        :type performer_provider: string
        :param performer_settings_data:
        :type performer_settings_data: dict
        :param disable_isolation:
        :type disable_isolation: bool
        :return:
        """
        environment_settings = settings.environments[environment_name]
        self.environment_name = environment_name
        self.project_name = settings.project

        # source
        if source_name:
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
        else:
            source_name, source_settings = list(environment_settings.sources.items())[0]

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

        # performer
        if not performer_provider:
            performer_settings = environment_settings.performer
            performer_provider = performer_settings.provider
            performer_settings_data = performer_settings.settings_data
        else:
            if performer_settings_data is None:
                performer_settings_data = {}

        performer = Performer(
            performer_provider,
            settings_data=performer_settings_data
        )

        # isolation
        if not disable_isolation:
            isolator_settings = environment_settings.isolator
            isolator_provider = isolator_settings.provider
            isolator_settings_data = isolator_settings.settings_data

            # TODO add codev version?
            ident = sorted(list(dict(
                project=settings.project,
                environment=environment_name,
                configuration=configuration_name,
                source_ident=source.ident,
                next_source_ident=next_source.ident if next_source else ''
            ).items()))

            self.performer = Isolator(isolator_provider, performer=performer, settings_data=isolator_settings_data, ident=ident)
        else:
            logging_config(perform=True)
            self.performer = performer

        # configuration
        if configuration_name:
            configuration_settings = environment_settings.configurations[configuration_name]
        else:
            # default configuration is the first configuration in environment
            configuration_name, configuration_settings = list(environment_settings.configurations.items())[0]

        self.configuration_name = configuration_name
        self.configuration = Configuration(
            configuration_settings, source,
            next_source=next_source,
            disable_isolation=disable_isolation,
            performer=self.performer
        )

    def deploy(self, input_vars):
        """
        Create machines, install and run provisioner

        :return: True if deployment is successfully realized
        :rtype: bool
        """
        return self.configuration.deploy(self.status, input_vars)

    def execute(self, script, arguments=None):
        """
        Run script.

        :param script: Script to execute
        :type script: str
        :param arguments: Arguments passed to script
        # :return: True if executed command returns 0
        :rtype: bool
        """
        logging_config(control_perform=True)
        try:
            self.configuration.execute_script(script, arguments, logger=command_logger)
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
        return self.configuration.destroy()

    @property
    def status(self):
        """
        Info about installation

        :return: installation status
        :rtype: dict
        """
        status = dict(
            project=self.project_name,
            environment=self.environment_name,
            configuration=self.configuration_name,
        )
        status.update(self.configuration.status)
        return status
