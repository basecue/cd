from os import getcwd
from .actual import ActualSource


class LiveSource(ActualSource):
    provider_name = 'live'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bidirectional = False

    def install(self, performer):
        performer.share(getcwd(), self.directory, bidirectional=self.bidirectional)

    def machine_install(self, machine):
        machine.share('.', self.directory, bidirectional=self.bidirectional)

    def process_options(self, options):
        if options == 'bidirectional':
            self.bidirectional = True
        elif options == '':
            self.bidirectional = False
        else:
            raise ValueError("Live source provider does not support options '{options}'".format(options=options))
        return options
