from typing import Any

import os

from codev.core.executor import BareExecutor
from codev.core.machines import Machine
from .actual import ActualSource


class LiveSource(ActualSource):
    provider_name = 'live'

    def __init__(self, options: str, *args: Any, **kwargs: Any):
        if options == 'bidirectional':
            self.bidirectional = True
        elif options == '':
            self.bidirectional = False
        else:
            raise ValueError(f"Live source provider does not support options '{options}'")
        super().__init__(options, *args, **kwargs)

    def install(self, executor: BareExecutor):
        executor.share(os.getcwd(), self.directory, bidirectional=self.bidirectional)

    def machine_install(self, machine: Machine):
        machine.share('.', self.directory, bidirectional=self.bidirectional)
