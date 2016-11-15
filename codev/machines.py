from .provider import Provider, ConfigurableProvider
from .performer import BaseProxyPerformer
from codev.debug import DebugSettings


class BaseMachine(BaseProxyPerformer):
    def __init__(self, *args, group=None, groups=None, **kwargs):
        self.group = group
        self.groups = groups
        super().__init__(*args, **kwargs)

    def exists(self):
        raise NotImplementedError()

    def is_started(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def create(self, settings, install_ssh_server=False, ssh_key=None):
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

    def __init__(self, performer, group, groups, *args, **kwargs):
        self.performer = performer
        self.group = group
        self.groups = [group] + groups
        super().__init__(*args, **kwargs)

    def idents(self):
        for i in range(1, self.settings.number + 1):
            ident = '%s_%000d' % (self.group, i)
            yield ident

    def create_machines(self):
        if DebugSettings.settings.ssh_copy:
            ssh_key = '%s\n' % self.performer.execute('ssh-add -L')
        else:
            ssh_key = None

        for ident in self.idents():
            machine = self.machine_class(self.performer, ident=ident, group=self.group, groups=self.groups)
            if not machine.exists():
                machine.create(self.settings, install_ssh_server=True, ssh_key=ssh_key)
            elif not machine.is_started():
                machine.start()

    @property
    def machines(self):
        for ident in self.idents():
            machine = self.machine_class(self.performer, ident=ident, group=self.group, groups=self.groups)
            if machine.exists():
                yield machine
