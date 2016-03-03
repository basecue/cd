from .provider import BaseProvider, ConfigurableProvider


class BaseInstallation(ConfigurableProvider):
    def __init__(self, options, *args, **kwargs):
        self.process_options(options)
        super(BaseInstallation, self).__init__(*args, **kwargs)

    def install(self, performer, directory):
        raise NotImplementedError()

    def process_options(self, options):
        raise NotImplementedError()

    @property
    def ident(self):
        raise NotImplementedError()


class Installation(BaseProvider):
    provider_class = BaseInstallation