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
    ):

        environment_settings = settings.environments[environment_name]
        self.environment_name = environment_name
        self.project_name = settings.project

        logging_config(perform=True)

        # configuration
        if configuration_name:
            configuration_settings = environment_settings.configurations[configuration_name]
        else:
            # default configuration is the first configuration in environment
            configuration_name, configuration_settings = list(environment_settings.configurations.items())[0]

        self.configuration_name = configuration_name
        self.configuration = Configuration(
            configuration_settings
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
