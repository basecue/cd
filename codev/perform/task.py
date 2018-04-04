from typing import Dict

import logging

from codev.core.executor import HasExecutor
from codev.core.provider import Provider
from codev.core.settings import HasSettings, ProviderSettings
from codev.perform.infrastructure import Infrastructure

logger = logging.getLogger(__name__)


class TaskSettings(ProviderSettings):
    # @property
    # def scripts(self):
    #     return TaskScriptsSettings(self.data.get('scripts', {}))

    @property
    def source(self) -> ProviderSettings:
        return ProviderSettings(self.data.get('source', {}))


class Task(Provider, HasSettings, HasExecutor):

    def run(self, infrastructure: Infrastructure, input_vars: Dict[str, str], source_directory: str) -> bool:
        raise NotImplementedError()
