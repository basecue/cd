from os import getcwd
from codev.source import Source


class LiveSource(Source):
    provider_name = 'live'

    def install(self, performer):
        performer.share(getcwd(), self.directory)

        with open('.codev') as codev_file:
            return codev_file

    def machine_install(self, machine):
        machine.share(self.directory, self.directory)
