from logging import getLogger

from codev.core import HasSettings
from codev.core.executor import HasExecutor
from codev.core.machines import Machine
from codev.core.settings import ProviderSettings, BaseSettings
from codev.core.utils import Ident

logger = getLogger(__name__)


class MachinesSettings(ProviderSettings):
    @property
    def groups(self):
        return self.data.get('groups', [])

    @property
    def number(self):
        return self.data.get('number', 1)


class InfrastructureSettings(BaseSettings):
    @property
    def machines(self):
        for machines_name, machines_settings in self.data.items():
            yield machines_name, MachinesSettings(data=machines_settings)


class Infrastructure(HasSettings, HasExecutor):
    settings_class = InfrastructureSettings

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
        logger.info('Creating infrastructure...')
        for machine in self.machines:
            machine.start_or_create()

    @property
    def machines(self):
        for machines_name, machines_settings in self.settings.machines:
            logger.debug(
                'Creating machines {machines_name}: {machines_settings}'.format(
                    machines_name=machines_name,
                    machines_settings=machines_settings
                )
            )
            for i in range(machines_settings.number):
                yield Machine(
                    machines_settings.provider,
                    ident=Ident(machines_name, i + 1),
                    executor=self.executor,
                    settings_data=machines_settings.settings_data,
                    groups=machines_settings.groups
                )

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
    @property
    def status(self):
        return [dict(ident=machine.ident, ip=machine.ip) for machine in self.machines]

