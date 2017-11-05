from codev.core.settings import HasSettings
from codev.core.utils import HasIdent
from .provider import Provider
from .executor import ProxyExecutor, HasExecutor
from .debug import DebugSettings


class BaseMachine(ProxyExecutor, HasSettings, HasIdent):
    # def __init__(self, *args, ident=None, group=None, groups=None, **kwargs):
    #     self.group = group
    #     self.groups = groups
    #     self.ident = ident
    #     super().__init__(*args, **kwargs)

    def exists(self):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def destroy(self):
        raise NotImplementedError()

    def is_started(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def start_or_create(self):
        if not self.exists():
            self.create()
            created = True
        else:
            created = False

        if not self.is_started():
            self.start()
        return created

    #
    # @property
    # def ip(self):
    #     #TODO rename to host
    #     raise NotImplementedError()


class Machine(Provider, BaseMachine):
    pass
    # def clone(self):
    #     raise NotImplementedError()

#
# class MachinesProvider(Provider, HasSettings, HasExecutor):
#     machine_class = BaseMachine
#
#     def __init__(self, group, groups, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.group = group
#         self.groups = [group] + groups
#
#     def idents(self):
#         for i in range(1, self.settings.number + 1):
#             ident = '%s-%000d' % (self.group.replace('_', '-'), i)
#             yield ident
#
#     def create_machines(self):
#         if DebugSettings.settings.ssh_copy:
#             ssh_key = '%s\n' % self.executor.execute('ssh-add -L')
#         else:
#             ssh_key = None
#
#         for ident in self.idents():
#             machine = self.machine_class(executor=self.executor, ident=ident, group=self.group, groups=self.groups)
#             if not machine.exists():
#                 machine.create(self.settings, ssh_key)
#             elif not machine.is_started():
#                 machine.start()
#
#     @property
#     def machines(self):
#         for ident in self.idents():
#             machine = self.machine_class(executor=self.executor, ident=ident, group=self.group, groups=self.groups)
#             if machine.exists():
#                 yield machine
