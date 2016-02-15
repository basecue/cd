from .provider import BaseProvider


class BaseMachinesProvider(object):
    def __init__(self, machines_name, performer, *args, **kwargs):
        self.machines_name = machines_name
        self.performer = performer
        super(BaseMachinesProvider, self).__init__(*args, **kwargs)


class MachinesProvider(BaseProvider):
    provider_class = BaseMachinesProvider
