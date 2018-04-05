from typing import Dict, Any

import logging

from codev.core import Codev, Status
from codev.core.debug import DebugSettings

from codev.control.configuration import ConfigurationControl
from .isolation import Isolation
from .log import logging_config
from .providers import *

logger = logging.getLogger(__name__)
# command_logger = getLogger('command')


class CodevControl(Codev):
    """
    Installation of project.
    """

    configuration_class = ConfigurationControl

    def __init__(
            self,
            *args: Any,
            source_name: str,
            source_option: str,
            next_source_name: str,
            next_source_option: str,
            **kwargs: Any
    ) -> None:
        logging_config(DebugSettings.settings.loglevel)

        super().__init__(*args, **kwargs)

        self.isolation = self.configuration.get_isolation(
            self.settings.project,
            source_name,
            source_option,
            next_source_name,
            next_source_option
        )

    def perform(self, input_vars: Dict) -> bool:
        """
        Create isolation and perform

        :return: True if deployment is successfully realized
        :rtype: bool
        """
        if not self.isolation.exists():
            self.isolation.create()

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
    def status(self) -> Status:
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
