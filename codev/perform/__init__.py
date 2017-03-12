from logging import getLogger

from codev.core.log import logging_config
from codev.core.infrastructure import Infrastructure
from codev.core.performer import CommandError, ScriptExecutor
from codev.core.providers.performers.local import LocalPerformer
from codev.core.debug import DebugSettings

from .provisioning import Provisioning


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

        super().__init__(performer=LocalPerformer())
        self.infrastructure = Infrastructure(self.performer, configuration_settings.infrastructure)
        self.provisioning = Provisioning(self.settings.provisions, performer=self.performer)

    def deploy(self, input_vars):
        """
        Create machines, install and run provisioner

        :return: True if deployment is successfully realized
        :rtype: bool
        """

        input_vars.update(DebugSettings.settings.load_vars)

        logger.info("Deploying project.")
        self.provisioning.provision(self.status, input_vars)

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
        Info about installation

        :return: installation status
        :rtype: dict
        """
        status = dict(
            project=self.project_name,
            environment=self.environment_name,
            configuration=self.configuration_name,
            infrastructure=self.infrastructure.status
        )
        return status
