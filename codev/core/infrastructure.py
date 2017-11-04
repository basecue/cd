from codev.core.executor import HasExecutor
from codev.core.settings import HasSettings
from codev.core.utils import Ident
from .machines import Machine


class Infrastructure(HasExecutor):
    def __init__(self, *args, settings, **kwargs):
        self.settings = settings
        super().__init__(*args, **kwargs)
    # def _machines_providers(self):
    #     for machinegroup_name, machinegroup_settings in self.settings.items():
    #         yield MachinesProvider(
    #             machinegroup_settings.provider,
    #             self.executor,
    #             machinegroup_name,
    #             machinegroup_settings.groups,
    #             settings_data=machinegroup_settings.settings_data
    #         )
    #
    # def get_machine_by_ident(self, ident):
    #     for machine in self.machines:
    #         if ident == machine.ident:
    #             return machine
    #     raise KeyError(ident)

    def create(self):
        for machines_name, machines_settings in self.settings.items():
            for i in range(machines_settings.number):
                machine = Machine(
                    machines_settings.provider,
                    ident=Ident(machines_name, i + 1),
                    executor=self.executor,
                    settings_data=machines_settings.settings_data
                )
                machine.start_or_create()


    # @property
    # def groups(self):
    #     groups = {}
    #     for machine in self.machines:
    #         for group in machine.groups:
    #             groups.setdefault(group, []).append(machine)
    #     return groups

    # @property
    # def main_groups(self):
    #     groups = {}
    #     for machine in self.machines:
    #         groups.setdefault(machine.group, []).append(machine)
    #     return groups
    #
    # @property
    # def status(self):
    #     return {
    #         group: [dict(ident=machine.ident, ip=machine.ip) for machine in machines]
    #         for group, machines in self.main_groups.items()
    #     }
