from logging import getLogger

from codev.core import CodevCore
from codev.core.performer import Performer
from codev.core.source import Source
from codev.core.debug import DebugSettings

from .isolation import Isolation

from .log import logging_config


logger = getLogger(__name__)
command_logger = getLogger('command')


class CodevControl(CodevCore):
    """
    Installation of project.
    """
    def __init__(
            self,
            settings,
            configuration_name,
            configuration_option='',
            source_name='',
            source_options='',
            next_source_name='',
            next_source_options=''
    ):
        logging_config(DebugSettings.settings.loglevel)

        super().__init__(settings, configuration_name, configuration_option)

        # source
        if source_name:
            try:
                source_settings = self.configuration_settings.sources[source_name]
            except KeyError as e:
                raise ValueError(
                    "Source '{source_name}' is not allowed source for configuration '{configuration_name}'.".format(
                        source_name=source_name,
                        configuration_name=configuration_name,
                        project_name=self.project_name
                    )
                ) from e
        else:
            source_name, source_settings = list(self.configuration_settings.sources.items())[0]

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
        performer_settings = self.configuration_settings.performer
        performer_provider = performer_settings.provider
        performer_settings_data = performer_settings.settings_data

        performer = Performer(
            performer_provider,
            settings_data=performer_settings_data
        )

        # configuration_option is not included, option can be run on the same isolation
        ident = ":".join((
            settings.project,
            configuration_name,
            source.ident,
            next_source.ident if next_source else ''
        ))

        self.source = source
        self.next_source = next_source
        self.isolation = Isolation(
            isolation_settings=self.configuration_settings.isolation,
            infrastructure_settings=self.configuration_settings.infrastructure,
            source=self.source,
            next_source=self.next_source,
            performer=performer,
            ident=ident
        )

    def run(self, input_vars):
        """
        Create machines, install and run task

        :return: True if deployment is successfully realized
        :rtype: bool
        """

        input_vars.update(DebugSettings.settings.load_vars)
        self.isolation.install(self.status)
        return self.isolation.run(self.status, input_vars)

    def destroy(self):
        """
        Destroy the isolation.

        :return: True if isolation is destroyed
        :rtype: bool
        """
        if self.isolation.exists():
            self.isolation.destroy()
            logger.info('Isolation has been destroyed.')
            return True
        else:
            logger.info('There is no such isolation.')
            return False

    @property
    def status(self):
        """
        Info about installation

        :return: installation status
        :rtype: dict
        """

        status = dict(
            project=self.project_name,
            configuration=self.configuration_name,
            configuration_option=self.configuration_option,
            source=self.source.name,
            source_options=self.source.options,
            source_ident=self.source.ident,
            next_source=self.next_source.name if self.next_source else '',
            next_source_options=self.next_source.options if self.next_source else '',
            next_source_ident=self.next_source.ident if self.next_source else '',
            isolation=self.isolation.status
        )

        return status
