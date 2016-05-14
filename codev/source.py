from contextlib import contextmanager
from .provider import Provider, ConfigurableProvider


class Source(Provider, ConfigurableProvider):
    def __init__(self, options, *args, **kwargs):
        self.ident = self.create_ident(self.process_options(options))
        self.options = options
        super().__init__(*args, **kwargs)

    @property
    def name(self):
        return self.__class__.provider_name

    def create_ident(self, ident):
        return '{name}_{ident}'.format(
            name=self.name,
            ident=ident
        )

    def install(self, performer):
        raise NotImplementedError()

    @contextmanager
    def open_codev_file(self, performer):
        with performer.change_directory(self.directory):
            with performer.get_fo('.codev') as codev_file:
                yield codev_file

    def machine_install(self, machine):
        pass

    def process_options(self, options):
        return options

    @property
    def id(self):
        raise NotImplementedError()

    @property
    def directory(self):
        return 'repository'
