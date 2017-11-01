from contextlib import contextmanager

from codev.core.executor import HasExecutor
from .provider import Provider, ConfigurableProvider


class Source(Provider, ConfigurableProvider, HasExecutor):
    def __init__(self, options, *args, **kwargs):
        self.options = options
        super().__init__(*args, **kwargs)

    @property
    def name(self):
        return self.__class__.provider_name

    def install(self):
        raise NotImplementedError()

    @contextmanager
    def open_codev_file(self):
        with self.executor.change_directory(self.directory):
            with self.executor.get_fo('.codev') as codev_file:
                yield codev_file

    def machine_install(self, machine):
        pass

    @property
    def directory(self):
        return 'repository'
