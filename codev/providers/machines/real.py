from codev.settings import BaseSettings
from codev.machines import MachinesProvider, BaseMachine


class RealMachine(BaseMachine):
    def exists(self):
        return True

    def is_started(self):
        return True

    def start(self):
        pass

    def create(self, distribution, release, install_ssh_server=False, ssh_key=None):
        pass

    def destroy(self):
        pass

    def stop(self):
        pass

    def install_packages(self, *packages):
        # TODO use ssh performer
        pass

    @property
    def ip(self):
        # TODO rename to host
        # TODO this is workaround
        return self.ident


class RealMachinesSettings(BaseSettings):
    @property
    def hosts(self):
        return self.data.get('hosts')


class RealMachinesProvider(MachinesProvider):
    provider_name = 'real'
    settings_class = RealMachinesSettings
    machine_class = RealMachine

    def idents(self):
        # TODO this is workaround
        for host in self.settings.hosts:
            yield host

