from logging import getLogger

from codev.core.infrastructure import Infrastructure
from codev.core.performer import CommandError
from codev.core.providers.performers.local import LocalPerformer
from codev.core.debug import DebugSettings

from .providers import *
from .provisioning import Provisioning

from .log import logging_config

logger = getLogger(__name__)
command_logger = getLogger('command')


class CodevPerform(object):
    """
    Installation of project.
    """
    def __init__(
            self,
            settings,
            environment_name,
            configuration_name='',
    ):
        logging_config(DebugSettings.settings.loglevel)

        environment_settings = settings.environments[environment_name]
        self.environment_name = environment_name
        self.project_name = settings.project


        # configuration
        if configuration_name:
            configuration_settings = environment_settings.configurations[configuration_name]
        else:
            # default configuration is the first configuration in environment
            configuration_name, configuration_settings = list(environment_settings.configurations.items())[0]

        self.configuration_name = configuration_name

        performer = LocalPerformer()
        self.infrastructure = Infrastructure(performer, configuration_settings.infrastructure)
        self.provisioning = Provisioning(configuration_settings.provisions, self.infrastructure, performer=performer)

    def run(self, input_vars):
        """
        Run provisioning

        :return: True if provisioning is successfully realized
        :rtype: bool
        """

        input_vars.update(DebugSettings.settings.load_vars)

        logger.info("Deploying project.")
        self.provisioning.run(self.status, input_vars)

    def execute(self, script, arguments=None):
        """
        Run script.

        :param script: Script to execute
        :type script: str
        :param arguments: Arguments passed to script
        :return: True if executed command returns 0
        :rtype: bool
        """
        arguments.update(self.status)
        try:
            self.provisioning.execute_script(script, arguments, logger=command_logger)
        except CommandError as e:
            logger.error(e)
            return False
        else:
            return True

    @property
    def status(self):
        """
        Info about provisioning

        :return: provisioning status
        :rtype: dict
        """
        status = dict(
            project=self.project_name,
            environment=self.environment_name,
            configuration=self.configuration_name,
            infrastructure=self.infrastructure.status
        )
        return status
