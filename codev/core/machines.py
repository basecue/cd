from typing import Iterable

from codev.core.settings import HasSettings
from codev.core.utils import HasIdent, Status
from .executor import ProxyExecutor
from .provider import Provider


class BaseMachine(HasSettings, ProxyExecutor, HasIdent):
    def exists(self) -> bool:
        raise NotImplementedError()

    def create(self) -> None:
        raise NotImplementedError()

    def destroy(self) -> None:
        raise NotImplementedError()

    def is_started(self) -> bool:
        raise NotImplementedError()

    def start(self) -> None:
        raise NotImplementedError()

    def stop(self) -> None:
        raise NotImplementedError()

    def start_or_create(self) -> None:
        if not self.exists():
            self.create()

        if not self.is_started():
            self.start()


class Machine(Provider, BaseMachine):
    # def clone(self):
    #     raise NotImplementedError()

    def __init__(self, *args, groups: Iterable = None, **kwargs) -> None:
        self.groups = groups or []
        super().__init__(*args, **kwargs)

    def ip(self):
        raise NotImplementedError

    def status(self) -> Status:
        return Status(ident=self.ident, ip=self.ip, groups=self.groups)
