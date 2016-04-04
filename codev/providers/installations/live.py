from codev.installation import Installation
from os import getcwd
from .actual import ActualInstallation
# experimental


class LiveInstallation(ActualInstallation):
    def install(self, performer):
        super(LiveInstallation, self).install(performer)
        performer.make_link(getcwd(), self.directory)

    def process_options(self, options):
        self.uid = options


Installation.register('live', LiveInstallation)
