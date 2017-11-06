from codev.core.executor import HasExecutor
from codev.core.settings import HasSettings
from .provider import Provider


class Source(Provider, HasSettings, HasExecutor):
    def install(self):
        raise NotImplementedError()
