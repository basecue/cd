from logging import getLogger

from codev.core.settings import YAMLSettingsReader
from codev.core import CodevCore
from codev.core.executor import Executor
from codev.core.source import Source
from codev.core.debug import DebugSettings
from codev.core.utils import Ident

from .isolation import Isolation

from .log import logging_config

from .providers import *

logger = getLogger(__name__)
# command_logger = getLogger('command')


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

        isolation_ident = Ident(
            self.project_name,
            self.configuration_name,
            source_name,
            source_options,
            next_source_name,
            next_source_options if next_source_name else ''
        )

        # executor
        executor_settings = self.configuration_settings.executor
        executor_provider = executor_settings.provider
        executor_settings_data = executor_settings.settings_data

        executor = Executor(
            executor_provider,
            settings_data=executor_settings_data
        )

        self.isolation = Isolation(
            self.configuration_settings.isolation.provider,
            settings_data=self.configuration_settings.isolation.settings_data,
            ident=isolation_ident,
            executor=executor,
        )

        self.source = Source(
            source_name,
            source_options,
            executor=self.isolation,
            settings_data=source_settings
        )

        if next_source_name:
            self.next_source = Source(
                next_source_name,
                next_source_options,
                executor=self.isolation,
                settings_data=source_settings
            )
        else:
            self.next_source = None

    def perform(self, input_vars):
        """
        Create isolation and perform

        :return: True if deployment is successfully realized
        :rtype: bool
        """

        created = self.isolation.start_or_create()

        if created or not self.next_source:
            current_source = self.source
        else:
            current_source = self.next_source

        return self.isolation.perform(current_source, self.configuration_name, self.configuration_option, input_vars)


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
        return dict(
            project=self.project_name,
            configuration=self.configuration_name,
            configuration_option=self.configuration_option,
            source=self.source.provider_name,
            source_options=self.source.options,
            next_source=self.next_source.name if self.next_source else '',
            next_source_options=self.next_source.options if self.next_source else '',
            isolation=self.isolation.status if self.isolation.exists() else ''
        )
