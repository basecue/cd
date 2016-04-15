from .provider import Provider, ConfigurableProvider
from .performer import BaseProxyPerformer


class BaseMachine(BaseProxyPerformer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MachinesProvider(Provider, ConfigurableProvider):
    def __init__(self, machines_name, performer, *args, **kwargs):
        self.machines_name = machines_name
        self.performer = performer
        super().__init__(*args, **kwargs)
