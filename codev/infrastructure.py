from .machines import MachinesProvider


class Infrastructure(object):
    def __init__(self, performer, settings):
        self.performer = performer
        self.settings = settings

    def _machines_providers(self):
        for machinegroup_name, machinegroup_settings in self.settings.items():
            yield MachinesProvider(
                machinegroup_settings.provider,
                self.performer,
                machinegroup_name,
                machinegroup_settings.groups,
                settings_data=machinegroup_settings.settings_data
            )

    def get_machine_by_ident(self, ident):
        for machine in self.machines:
            if ident == machine.ident:
                return machine
        raise KeyError(ident)

    def create_machines(self):
        for machinegroup_provider in self._machines_providers():
            machinegroup_provider.create_machines()

    @property
    def machines(self):
        for machines_provider in self._machines_providers():
            for machine in machines_provider.machines:
                yield machine

    # @property
    # def groups(self):
    #     groups = {}
    #     for machine in self.machines:
    #         for group in machine.groups:
    #             groups.setdefault(group, []).append(machine)
    #     return groups

    @property
    def main_groups(self):
        groups = {}
        for machine in self.machines:
            groups.setdefault(machine.group, []).append(machine)
        return groups

    @property
    def info(self):
        return {
            group: [dict(ident=machine.ident, ip=machine.ip) for machine in machines]
            for group, machines in self.main_groups.items()
        }
