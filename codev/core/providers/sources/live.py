from os import getcwd

from .actual import ActualSource


class LiveSource(ActualSource):
    provider_name = 'live'

    def __init__(self, options, *args, **kwargs):
        if options == 'bidirectional':
            self.bidirectional = True
        elif options == '':
            self.bidirectional = False
        else:
            raise ValueError(f"Live source provider does not support options '{options}'")
        super().__init__(options, *args, **kwargs)

    def install(self, executor):
        executor.share(getcwd(), self.directory, bidirectional=self.bidirectional)

    def machine_install(self, machine):
        machine.share('.', self.directory, bidirectional=self.bidirectional)
