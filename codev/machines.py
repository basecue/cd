from .provider import Provider, ConfigurableProvider
from .performer import BaseProxyPerformer


class BaseMachine(BaseProxyPerformer):
    def exists(self):
        raise NotImplementedError()

    def is_started(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def create(self, distribution, release, install_ssh_server=False, ssh_key=None):
        raise NotImplementedError()

    def destroy(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    @property
    def ip(self):
        #TODO rename to host
        raise NotImplementedError()


class MachinesProvider(Provider, ConfigurableProvider):
    machine_class = BaseMachine

    def __init__(self, ident, performer, *args, **kwargs):
        self.ident = ident
        self.performer = performer
        super().__init__(*args, **kwargs)

    def idents(self):
        for i in range(1, self.settings.number + 1):
            ident = '%s_%000d' % (self.ident, i)
            yield ident

    def machines(self, create=False, ssh_key=None):
        for ident in self.idents():
            machine = self.machine_class(self.performer, ident=ident)
            if create and not machine.exists():
                machine.create(self.settings.distribution, self.settings.release, install_ssh_server=True, ssh_key=ssh_key)
            elif create and not machine.is_started():
                machine.start()

            if create or machine.exists():
                yield machine
