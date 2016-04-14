from codev.source import Source
from os import getcwd
from .actual import ActualSource
# experimental


class LiveSource(ActualSource):
    def install(self, performer):
        super(LiveSource, self).install(performer)
        performer.make_link(getcwd(), self.directory)

    def process_options(self, options):
        self.uid = options


Source.register('live', LiveSource)
