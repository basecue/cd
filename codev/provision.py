from .provider import BaseProvider, ConfigurableProvider


class BaseProvision(ConfigurableProvider):
    def __init__(self, performer, infrastructure_name, *args, **kwargs):
        self.performer = performer
        self.infrastructure_name = infrastructure_name
        super(BaseProvision, self).__init__(*args, **kwargs)

    def install(self):
        raise NotImplementedError()

    def run(self, machines):
        raise NotImplementedError()


class Provision(BaseProvider):
    provider_class = BaseProvision
