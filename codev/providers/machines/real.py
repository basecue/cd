from codev.settings import BaseSettings
from codev.machines import MachinesProvider, BaseMachine


class RealMachine(BaseMachine):
    def __init__(self, ip):
        self.ip = ip
        #TODO


class RealMachinesSettings(BaseSettings):
    @property
    def hosts(self):
        return self.data.get('hosts')


class RealMachinesProvider(MachinesProvider):
    provider_name = 'real'
    settings_class = RealMachinesSettings

