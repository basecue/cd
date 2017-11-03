from codev.core.executor import HasExecutor
from codev.core.provider import Provider, HasSettings


class Task(Provider, HasSettings, HasExecutor):

    def prepare(self):
        raise NotImplementedError()

    def run(self, infrastructure, script_info, input_vars):
        raise NotImplementedError()

