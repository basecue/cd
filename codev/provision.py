from .provider import BaseProvider, ConfigurableProvider
from .performer import BaseProxyPerformer


class BaseProvisioner(BaseProxyPerformer, ConfigurableProvider):

    def install(self):
        raise NotImplementedError()

    def run(self, infrastructure):
        raise NotImplementedError()


class Provisioner(BaseProvider):
    provider_class = BaseProvisioner
