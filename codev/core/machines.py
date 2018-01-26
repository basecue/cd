from codev.core.settings import HasSettings
from codev.core.utils import HasIdent
from .executor import ProxyExecutor
from .provider import Provider


class BaseMachine(HasSettings, ProxyExecutor, HasIdent):
    def exists(self):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def destroy(self):
        raise NotImplementedError()

    def is_started(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def start_or_create(self):
        if not self.exists():
            self.create()

        if not self.is_started():
            self.start()


class Machine(Provider, BaseMachine):
    # def clone(self):
    #     raise NotImplementedError()

    def __init__(self, *args, groups=None, **kwargs):
        self.groups = groups or []
        super().__init__(*args, **kwargs)
