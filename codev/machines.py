from .provider import BaseProvider, ConfigurableProvider
from .performer import BaseRunner, BasePerformer, CommandError


class BaseMachine(BaseRunner, BasePerformer):
    def __init__(self, *args, **kwargs):
        super(BaseMachine, self).__init__(*args, **kwargs)


class BaseMachinesProvider(ConfigurableProvider):
    def __init__(self, machines_name, performer, *args, **kwargs):
        self.machines_name = machines_name
        self.performer = performer
        super(BaseMachinesProvider, self).__init__(*args, **kwargs)


class MachinesProvider(BaseProvider):
    provider_class = BaseMachinesProvider
