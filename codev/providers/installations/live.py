from codev.installation import Installation, BaseInstallation
from os import getcwd
from time import sleep
# experimental
# TODO inherit from actual and after classic installation create the link with make_link


class LivelInstallation(BaseInstallation):
    def install(self, performer):
        performer.make_link(getcwd(), self.directory)
        sleep(5)

    def process_options(self, options):
        self.uid = options

    @property
    def id(self):
        return self.uid

Installation.register('live', LivelInstallation)
