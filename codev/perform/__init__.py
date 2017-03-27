from logging import getLogger

from codev.core import CodevCore
from codev.core.infrastructure import Infrastructure
from codev.core.performer import CommandError
from codev.core.providers.performers.local import LocalPerformer
from codev.core.debug import DebugSettings

from .providers import *
from .runner import TasksRunner

from .log import logging_config

logger = getLogger(__name__)
command_logger = getLogger('command')


class CodevPerform(CodevCore):
    """
    Installation of project.
    """
    def __init__(
            self,
            settings,
            configuration_name,
            configuration_option=''
    ):
        logging_config(DebugSettings.settings.loglevel)

        super().__init__(settings, configuration_name, configuration_option)

        performer = LocalPerformer()
        self.infrastructure = Infrastructure(performer, self.configuration_settings.infrastructure)
        self.tasks_runner = TasksRunner(self.configuration_settings.tasks, self.infrastructure, performer=performer)

    def run(self, input_vars):
        """
        Run runner

        :return: True if runner is successfully realized
        :rtype: bool
        """

        input_vars.update(DebugSettings.settings.load_vars)

        # logger.info("Run configuration {configuration}.")
        return self.tasks_runner.run(self.status, input_vars)

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
            self.tasks_runner.execute_script(script, arguments, logger=command_logger)
        except CommandError as e:
            logger.error(e)
            return False
        else:
            return True

    @property
    def status(self):
        """
        Info about runner

        :return: runner status
        :rtype: dict
        """
        status = dict(
            project=self.project_name,
            configuration=self.configuration_name,
            configuration_option=self.configuration_option,
            infrastructure=self.infrastructure.status
        )
        return status
