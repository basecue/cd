from codev.core.settings import BaseSettings
from codev.core.machines import Machine


class RealMachine(Machine):
    provider_name = 'real'
    # settings_class = RealMachineSettings

    def exists(self):
        return True

    def is_started(self):
        return True

    def start(self):
        pass

    def create(self, settings, ssh_key):
        pass

    def destroy(self):
        pass

    def stop(self):
        pass

    def install_packages(self, *packages):
        # TODO use ssh executor
        pass

    @property
    def ip(self):
        # TODO rename to host
        # TODO this is workaround
        return self.ident


