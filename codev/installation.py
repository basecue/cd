from .configuration import Configuration
from .source import Source
from .logging import logging_config
from .performer import CommandError, Performer
from .isolator import Isolator

from logging import getLogger

logger = getLogger(__name__)


class Installation(object):
    """
    Installation of project.
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
            performer_specific=None,
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
        :param performer_specific:
        :type performer_specific: dict
        :param disable_isolation:
        :type disable_isolation: bool
        :return:
        """
        environment_settings = settings.environments[environment_name]
        self.environment_name = environment_name
        self.project_name = settings.project

        # source
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

        # performer
        if not performer_provider:
            performer_settings = environment_settings.performer
            performer_provider = performer_settings.provider
            performer_specific = performer_settings.specific
        else:
            if performer_specific is None:
                performer_specific = {}

        performer = Performer(
            performer_provider,
            settings_data=performer_specific
        )

        # isolation
        if not disable_isolation:
            isolator_settings = environment_settings.isolator
            isolator_provider = isolator_settings.provider
            isolator_specific = isolator_settings.specific

            # TODO add codev version?
            ident = sorted(list(dict(
                project=settings.project,
                environment=environment_name,
                configuration=configuration_name,
                source_ident=source.ident,
                next_source_ident=next_source.ident if next_source else ''
            ).items()))

            self.performer = Isolator(isolator_provider, performer, settings_data=isolator_specific, ident=ident)
        else:
            logging_config(perform=True)
            self.performer = performer

        # configuration
        configuration_settings = environment_settings.configurations[configuration_name]
        self.configuration_name = configuration_name
        self.configuration = Configuration(
            self.performer, configuration_settings, source, next_source, disable_isolation
        )

    def deploy(self):
        """
        Create machines, install and run provisioner

        :return: True if deployment is successfully realized
        :rtype: bool
        """
        return self.configuration.deploy(self.info)

    def run(self, script, arguments=None):
        """
        Run script.

        :param script: Script to execute
        :type script: str
        :param arguments: Arguments passed to script
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
        return self.configuration.destroy()

    @property
    def info(self):
        """
        Info about installation

        :return: installation info
        :rtype: dict
        """
        info = dict(
            project=self.project_name,
            environment=self.environment_name,
            configuration=self.configuration_name,
        )
        info.update(self.configuration.info)
        return info
