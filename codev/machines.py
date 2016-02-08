from .provider import BaseProvider


class BaseMachinesProvider(object):
    def __init__(self, machines_name, performer, configuration_data):
        self.machines_name = machines_name
        self.performer = performer
        self.configuration_data = configuration_data


class ConfigurableMachinesProvider(BaseMachinesProvider):
    configuration_class = None

    def __init__(self, *args, **kwargs):
        super(ConfigurableMachinesProvider, self).__init__(*args, **kwargs)
        self.configuration = self.__class__.configuration_class(self.configuration_data)


class MachinesProvider(BaseProvider):
    provider_class = BaseMachinesProvider
