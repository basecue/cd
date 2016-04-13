from .provider import BaseProvider, ConfigurableProvider
from .performer import BaseProxyPerformer


class BaseProvisioner(ConfigurableProvider):
    def __init__(self, performer, *args, **kwargs):
        super(BaseProvisioner, self).__init__(*args, **kwargs)
        self.performer = BaseProxyPerformer(performer)

    def install(self):
        raise NotImplementedError()

    def run(self, infrastructure):
        raise NotImplementedError()


class Provisioner(BaseProvider):
    provider_class = BaseProvisioner
