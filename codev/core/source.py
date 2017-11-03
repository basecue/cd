from codev.core.executor import HasExecutor
from codev.core.settings import HasSettings
from .provider import Provider


class Source(Provider, HasSettings, HasExecutor):
    def __init__(self, options, *args, **kwargs):
        self.options = options
        super().__init__(*args, **kwargs)

    def install(self):
        raise NotImplementedError()
