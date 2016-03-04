from .provider import BaseProvider, ConfigurableProvider


class BaseInstallation(ConfigurableProvider):
    def __init__(self, options, *args, **kwargs):
        self.process_options(options)
        self.options = options
        super(BaseInstallation, self).__init__(*args, **kwargs)

    @property
    def name(self):
        return self.__class__.provider_name

    @property
    def ident(self):
        return '{name}_{ident}'.format(
            name=self.name,
            ident=self.id
        )

    def install(self, performer):
        raise NotImplementedError()

    def process_options(self, options):
        raise NotImplementedError()

    @property
    def id(self):
        raise NotImplementedError()

    @property
    def directory(self):
        return 'repository'


class Installation(BaseProvider):
    provider_class = BaseInstallation