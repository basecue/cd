from .machines import MachinesProvider


class Infrastructure(object):
    def __init__(self, performer, settings):
        self.performer = performer
        self.settings = settings
        self.machines_groups = {}

    def create(self):
        pub_key = '%s\n' % self.performer.execute('ssh-add -L')
        for machines_name, machines_settings in self.settings.items():
            machines_provider = MachinesProvider(
                machines_settings.provider,
                machines_name, self.performer, settings_data=machines_settings.specific
            )
            self.machines_groups[machines_name] = machines_provider.machines(create=True, pub_key=pub_key)

    def machines(self):
        for machine_group_name, machines in self.machines_groups:
            for machine in machines:
                yield machine

    def machines_info(self):
        return {
            'machine_{ident}'.format(ident=machine.ident): machine.ip for machine in self.machines()
        }
