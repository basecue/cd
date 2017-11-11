from codev.core.settings import HasSettings
from .provider import Provider


class Source(Provider, HasSettings):
    def install(self, executor):
        raise NotImplementedError()