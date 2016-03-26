from codev.installation import Installation, BaseInstallation
from os import getcwd
# experimental


class LivelInstallation(BaseInstallation):
    def install(self, performer):
        performer.make_link(getcwd(), self.directory)

    def process_options(self, options):
        self.uid = options

    @property
    def id(self):
        return self.uid

Installation.register('live', LivelInstallation)
