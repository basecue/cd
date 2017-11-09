from logging import getLogger

from codev.core import CodevCore
from codev.core.debug import DebugSettings
from codev.core.infrastructure import Infrastructure
from codev.core.providers.executors.local import LocalExecutor
from codev.perform.task import Task
from .log import logging_config
from .providers import *

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

        self.executor = LocalExecutor()
        self.infrastructure = Infrastructure(
            executor=self.executor,
            settings=self.configuration_settings.infrastructure
        )

    def run(self, input_vars):
        """
        Run runner

        :return: True if runner is successfully realized
        :rtype: bool
        """

        input_vars.update(DebugSettings.settings.load_vars)

        self.infrastructure.create()

        for task_name, task_settings in self.configuration_settings.tasks.items():
            task = Task(task_settings.provider, executor=self.executor, settings_data=task_settings.settings_data)

            name = " '{}'".format(task_name) if task_name else ''
            logger.info("Preparing task{name}...".format(name=name))
            task.prepare()

            logger.info("Running task{name}...".format(name=name))
            task.run(self.infrastructure, input_vars)


    # def execute(self, script, arguments=None):
    #     """
    #     Run script.
    #
    #     :param script: Script to execute
    #     :type script: str
    #     :param arguments: Arguments passed to script
    #     :return: True if executed command returns 0
    #     :rtype: bool
    #     """
    #     arguments.update(self.status)
    #     try:
    #         self.tasks_runner.execute_script(script, arguments, logger=command_logger)
    #     except CommandError as e:
    #         logger.error(e)
    #         return False
    #     else:
    #         return True

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
