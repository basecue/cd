from os import getcwd
from .actual import ActualSource


class LiveSource(ActualSource):
    provider_name = 'live'

    def install(self, performer):
        super().install(performer)
        performer.make_link(getcwd(), self.directory)

    def process_options(self, options):
        self.uid = options
