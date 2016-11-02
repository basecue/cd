from codev.provider import Provider, ConfigurableProvider


class AnsibleSource(Provider, ConfigurableProvider):
    def __init__(self, performer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.performer = performer

    def install(self):
        raise NotImplementedError()

    @property
    def directory(self):
        raise NotImplementedError()
