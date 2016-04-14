from .provider import Provider, ConfigurableProvider
from .performer import BaseProxyPerformer


class BaseMachine(BaseProxyPerformer):
    def __init__(self, *args, **kwargs):
        super(BaseMachine, self).__init__(*args, **kwargs)


class MachinesProvider(Provider, ConfigurableProvider):
    def __init__(self, machines_name, performer, *args, **kwargs):
        self.machines_name = machines_name
        self.performer = performer
        super(MachinesProvider, self).__init__(*args, **kwargs)
