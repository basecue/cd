from typing import Dict, TypeVar

from codev.core.executor import BareExecutor
from codev.core.settings import HasSettings
from codev.core.utils import Status
from .provider import Provider

SourceType = TypeVar('SourceType', bound='Source')


class Source(Provider, HasSettings):

    def __init__(self, *args, option: str, **kwargs):
        self.option = option
        super().__init__(*args, **kwargs)

    def install(self, executor: BareExecutor) -> None:
        raise NotImplementedError()

    @classmethod
    def get(cls, name: str, sources: Dict, option: str, default: bool = True) -> SourceType:
        # TODO refactorize
        if not name:
            if default:
                name = list(sources.keys())[0]
            else:
                return None
        try:
            return cls(name, settings_data=sources[name], option=option)
        except KeyError:
            raise ValueError()

    @property
    def status(self) -> Status:
        return Status(
            name=self.provider_name,
            option=self.option
        )
