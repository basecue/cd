from .provider import BaseProvider, ConfigurableProvider
from .performer import BaseRunner


class BaseProvisioner(BaseRunner, ConfigurableProvider):

    def install(self):
        raise NotImplementedError()

    def run(self, infrastructure):
        raise NotImplementedError()


class Provisioner(BaseProvider):
    provider_class = BaseProvisioner
