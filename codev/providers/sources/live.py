from os import getcwd
from codev.source import Source


class LiveSource(Source):
    provider_name = 'live'

    def install(self, performer):
        performer.share(getcwd(), self.directory)

        return open('.codev')

    def machine_install(self, machine):
        machine.share(self.directory, self.directory)
