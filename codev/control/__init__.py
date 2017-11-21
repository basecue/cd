from logging import getLogger

from codev.control.configuration import ConfigurationControl
from codev.core import Codev
from codev.core.debug import DebugSettings
from codev.core.utils import Ident
from .isolation import Isolation
from .log import logging_config
from .providers import *

logger = getLogger(__name__)
# command_logger = getLogger('command')


class CodevControl(Codev):
    """
    Installation of project.
    """

    configuration_class = ConfigurationControl

    def __init__(
            self,
            *args,
            source_name='',
            source_option='',
            next_source_name='',
            next_source_option='',
            **kwargs
    ):
        logging_config(DebugSettings.settings.loglevel)

        super().__init__(*args, **kwargs)

        isolation_ident = Ident(
            self.settings.project,
            self.configuration.name,
            source_name,
            source_option,
            next_source_name,
            next_source_option if next_source_name else ''
        )

        # executor

        self.isolation = self.configuration.get_isolation(ident=isolation_ident)

        # FIXME refactorize to isolation
        try:
            self.source = self.configuration.get_source(source_name, source_option)
        except ValueError:
            raise ValueError(
                "Source '{source_name}' is not allowed source for configuration '{configuration_name}'.".format(
                    source_name=source_name,
                    configuration_name=self.configuration.name
                )
            )

        if next_source_name:
            self.next_source = self.configuration.get_source(next_source_name, next_source_option)
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

        codev = self.isolation.install_codev(current_source)
        return self.isolation.perform(codev, input_vars)


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
        status = super().status
        status.update(
            source=self.source.status,
            next_source=self.next_source.status if self.next_source else '',
            isolation=self.isolation.status
        )
        return status
