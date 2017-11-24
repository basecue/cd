from logging import getLogger

from codev.control.configuration import ConfigurationControl
from codev.core import Codev
from codev.core.debug import DebugSettings
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
            source_name, source_option, next_source_name, next_source_option,
            **kwargs
    ):
        logging_config(DebugSettings.settings.loglevel)

        super().__init__(*args, **kwargs)

        self.isolation = self.configuration.get_isolation(
            self.settings.project,
            source_name,
            source_option,
            next_source_name,
            next_source_option
        )

    def perform(self, input_vars):
        """
        Create isolation and perform

        :return: True if deployment is successfully realized
        :rtype: bool
        """

        return self.isolation.perform(input_vars)


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
            configuration=self.configuration.status,
            isolation=self.isolation.status
        )
        return status
