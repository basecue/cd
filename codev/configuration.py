from logging import getLogger
from .machines import MachinesProvider
from hashlib import md5
from .isolation import Isolation

logger = getLogger(__name__)


class Configuration(object):
    def __init__(self, name, settings):
        self.name = name
        self.settings = settings

    # TODO refactorize - Infrastructure class
    def infrastructure(self, performer, create=False):
        settings = self.settings.infrastructure
        machines_groups = {}
        if create:
            pub_key = '%s\n' % performer.execute('ssh-add -L')
        else:
            pub_key = None
        for machines_name, machines_settings in settings.items():
            machines_provider = MachinesProvider(
                machines_settings.provider,
                machines_name, performer, settings_data=machines_settings.specific
            )
            machines_groups[machines_name] = machines_provider.machines(create=create, pub_key=pub_key)
        return machines_groups

    def machines(self, performer):
        for machine_group_name, machines in self.infrastructure(performer).items():
            for machine in machines:
                yield machine

    def machines_info(self, performer):
        return {
            'machine_{ident}'.format(ident=machine.ident): machine.ip for machine in self.machines(performer)
        }

    ###

    def isolation(self, performer, source, next_source, ident):
        isolation_settings = self.settings.isolation
        return Isolation(
            isolation_settings.provider,
            isolation_settings.scripts,
            isolation_settings.connectivity,
            self,
            source,
            next_source,
            performer,
            ident=md5(ident.encode()).hexdigest()
        )
