from logging import getLogger

from codev.core.settings import YAMLSettingsReader
from .isolator import Isolator
from codev.core import CodevCore
from codev.core.performer import Performer
from codev.core.source import Source
from codev.core.debug import DebugSettings

from .isolator import Isolator

from .log import logging_config

from .providers import *

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

        self.source = source
        self.next_source = next_source

        self.isolator = Isolator(
            self.configuration_settings.isolation.provider,
            settings_data=self.configuration_settings.isolation,
            performer=performer,
        )

    @property
    def isolation_ident(self):
        return tuple(filter(None, [
            self.project_name,
            self.configuration_name,
            self.source.name,
            self.source.options,
            self.next_source.name if self.next_source else '',
            self.next_source.options if self.next_source else ''
        ]))

    def perform(self, input_vars):
        """
        Create isolation and perform

        :return: True if deployment is successfully realized
        :rtype: bool
        """

        isolation, created = self.isolator.create(self.isolation_ident)

        if created or not self.next_source:
            current_source = self.source
        else:
            current_source = self.next_source

        current_source.install(isolation)

        with current_source.open_codev_file(isolation) as codev_file:
            current_settings = YAMLSettingsReader().from_yaml(codev_file)

        codev_version = current_settings.version
        isolation.install(codev_version)

        load_vars = {**current_settings.loaded_vars, **input_vars}
        load_vars.update(DebugSettings.settings.load_vars)

        return isolation.perform(self.configuration_name, self.configuration_option, load_vars)

    # FIXME
    # def destroy(self):
    #     """
    #     Destroy the isolation.
    #
    #     :return: True if isolation is destroyed
    #     :rtype: bool
    #     """
    #     if self.isolation.exists():
    #         self.isolation.destroy()
    #         logger.info('Isolation has been destroyed.')
    #         return True
    #     else:
    #         logger.info('There is no such isolation.')
    #         return False

    @property
    def status(self):
        """
        Info about installation

        :return: installation status
        :rtype: dict
        """
        isolation = self.isolator.get(self.isolation_ident)

        return dict(
            project=self.project_name,
            configuration=self.configuration_name,
            configuration_option=self.configuration_option,
            source=self.source.name,
            source_options=self.source.options,
            next_source=self.next_source.name if self.next_source else '',
            next_source_options=self.next_source.options if self.next_source else '',
            isolation=isolation.status if isolation else ''
        )
