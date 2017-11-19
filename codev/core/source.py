from codev.core.settings import HasSettings
from codev.core.utils import Status
from .provider import Provider


class Source(Provider, HasSettings):

    def install(self, executor):
        raise NotImplementedError()

    @classmethod
    def get(cls, name, sources, option):
        if not name:
            name = list(sources.keys())[0]

        try:
            return cls(name, settings_data=sources[name], option=option)
        except KeyError:
            raise ValueError()

    @property
    def status(self):
        return Status(
            name=self.provider_name,
            option=self.option
        )