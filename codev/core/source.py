from contextlib import contextmanager

from .provider import Provider, ConfigurableProvider


class Source(Provider, ConfigurableProvider):
    def __init__(self, options, *args, **kwargs):
        self.options = options
        super().__init__(*args, **kwargs)

    @property
    def name(self):
        return self.__class__.provider_name

    def install(self, performer):
        raise NotImplementedError()

    @contextmanager
    def open_codev_file(self, performer):
        with performer.change_directory(self.directory):
            with performer.get_fo('.codev') as codev_file:
                yield codev_file

    def machine_install(self, machine):
        pass

    @property
    def directory(self):
        return 'repository'
