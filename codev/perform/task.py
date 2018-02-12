from logging import getLogger

from codev.core.executor import HasExecutor
from codev.core.provider import Provider
from codev.core.settings import HasSettings, ProviderSettings

logger = getLogger(__name__)


class TaskSettings(ProviderSettings):
    # @property
    # def scripts(self):
    #     return TaskScriptsSettings(self.data.get('scripts', {}))

    @property
    def source(self):
        return ProviderSettings(self.data.get('source', {}))


class Task(Provider, HasSettings, HasExecutor):

    def run(self, infrastructure, input_vars, source_directory):
        raise NotImplementedError()
