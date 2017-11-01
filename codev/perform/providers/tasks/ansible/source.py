from codev.core.provider import Provider, ConfigurableProvider


class AnsibleSource(Provider, ConfigurableProvider):
    def __init__(self, executor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executor = executor

    def install(self):
        raise NotImplementedError()

    @property
    def directory(self):
        raise NotImplementedError()
