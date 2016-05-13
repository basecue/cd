from .machines import MachinesProvider


class Infrastructure(object):
    def __init__(self, performer, settings):
        self.performer = performer
        self.settings = settings

    def _machines_providers(self):
        for machines_ident, machines_settings in self.settings.items():
            yield MachinesProvider(
                machines_settings.provider,
                machines_ident, self.performer, settings_data=machines_settings.specific
            )

    def get_machine_by_ident(self, ident):
        for machine_group, machines in self.machines_groups().items():
            for machine in machines:
                if ident == machine.ident:
                    return machine
        raise KeyError(ident)

    def machines_groups(self, source=None, create=False):
        if create:
            ssh_key = '%s\n' % self.performer.execute('ssh-add -L')
        else:
            ssh_key = None

        return {
            machines_provider.ident: [
                machine for machine in machines_provider.machines(source=source, create=create, ssh_key=ssh_key)
            ] for machines_provider in self._machines_providers()
        }

    @property
    def info(self):
        return {
            machines_group: [
                dict(ident=machine.ident, ip=machine.ip) for machine in machines
            ] for machines_group, machines in self.machines_groups().items()
        }
