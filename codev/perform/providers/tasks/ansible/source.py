from codev.core.executor import HasExecutor
from codev.core.provider import Provider, HasSettings


class AnsibleSource(Provider, HasSettings, HasExecutor):

    def install(self):
        raise NotImplementedError()

    @property
    def directory(self):
        raise NotImplementedError()
