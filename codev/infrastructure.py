from .machines import MachinesProvider


class Infrastructure(object):
    def __init__(self, performer, settings):
        self.performer = performer
        self.settings = settings

    def _machines_providers(self):
        for machinegroup_name, machinegroup_settings in self.settings.items():
            yield MachinesProvider(
                machinegroup_settings.provider,
                self.performer, machinegroup_name, machinegroup_settings.groups, settings_data=machinegroup_settings.settings_data
            )

    def get_machine_by_ident(self, ident):
        for machine in self.machines:
            if ident == machine.ident:
                return machine
        raise KeyError(ident)

    def create_machines(self):
        for machinegroup_provider in self._machines_providers():
            for machine in machinegroup_provider.create_machines():
                yield machine

    @property
    def machines(self):
        for machines_provider in self._machines_providers():
            for machine in machines_provider.machines:
                yield machine

    @property
    def info(self):
        machine_groups = {}
        for machine in self.machines:
            machine_groups.setdefault(machine.group, []).append(dict(ident=machine.ident, ip=machine.ip))

        return machine_groups
