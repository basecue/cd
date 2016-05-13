from os import getcwd
from .actual import ActualSource


class LiveSource(ActualSource):
    provider_name = 'live'

    def install(self, performer):
        performer.share(getcwd(), self.directory)

    def machine_install(self, machine):
        machine.share(self.directory, self.directory)
