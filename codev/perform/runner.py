from logging import getLogger

from codev.core.executor import CommandError, HasExecutor

from .task import Task


logger = getLogger(__name__)


class TasksRunner(HasExecutor):
    def __init__(self, tasks, infrastructure, *args, **kwargs):
        self.tasks = tasks
        self.infrastructure = infrastructure
        super().__init__(*args, **kwargs)

    def run(self, input_vars):
        for task_name, task_settings in self.tasks.items():
            task = Task(task_settings.provider, executor=self.executor, settings_data=task_settings.settings_data)

            name = " '{}'".format(task_name) if task_name else ''
            logger.info("Preparing task{name}...".format(name=name))
            task.prepare()

            logger.info("Running task{name}...".format(name=name))
            task.run(self.infrastructure, input_vars)

