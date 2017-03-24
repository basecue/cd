from logging import getLogger

from codev.core.performer import ScriptExecutor, CommandError

from .task import Task


logger = getLogger(__name__)


class TasksRunner(ScriptExecutor):
    def __init__(self, tasks, infrastructure, *args, **kwargs):
        self.tasks = tasks
        self.infrastructure = infrastructure
        super().__init__(*args, **kwargs)

    def run(self, status, input_vars):
        # TODO
        # scripts = self.settings.scripts

        try:
            # TODO
            # self.execute_scripts(scripts.onstart, status)

            self._run(self.infrastructure, status, input_vars)

        except CommandError as e:
            # TODO
            # self.execute_scripts_onerror(scripts.onerror, status, e, logger=logger)
            logger.error(e.error)
            return False
        else:
            try:
                # TODO
                # self.execute_scripts(scripts.onsuccess, status)
                return True
            except CommandError as e:
                # TODO
                # self.execute_scripts_onerror(scripts.onerror, status, e, logger=logger)
                logger.error(e.error)
                return False

    def _run(self, infrastructure, script_info, input_vars):
        """

        :param infrastructure: infrastructure.Infrastructure
        :param script_info: dict
        :return:
        """

        logger.info('Creating machines...')
        infrastructure.create_machines()

        script_info.update(infrastructure=infrastructure.status)

        for task_name, task_settings in self.tasks.items():
            # TODO
            # scripts = task_settings.scripts

            try:
                # TODO
                # self.execute_scripts(scripts.onstart, script_info)

                task = Task(task_settings.provider, performer=self.performer, settings_data=task_settings.settings_data)

                name = " '{}'".format(task_name) if task_name else ''
                logger.info("Preparing task{name}...".format(name=name))
                task.prepare()

                logger.info("Running task{name}...".format(name=name))
                task.run(infrastructure, script_info, input_vars)

            except CommandError as e:
                # TODO
                # self.execute_scripts_onerror(scripts.onerror, script_info, e, logger=logger)
                raise
            else:
                try:
                    # TODO
                    # self.execute_scripts(scripts.onsuccess, script_info)
                    # logger.info("Task{name} has been succesfully executed.".format(name=name))
                    pass
                except CommandError as e:
                    # TODO
                    # self.execute_scripts_onerror(scripts.onerror, script_info, e, logger=logger)
                    raise
