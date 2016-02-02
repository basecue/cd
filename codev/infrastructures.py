
class LXCInfrastructure(object):
    def __init__(self, machines):
        # self.performer = LocalPerformer()
        self.configuration = machines


INFRASTRUCTURE_PROVIDERS_BY_NAME = {
    'lxc': LXCInfrastructure
}


class Infrastructure(object):
    def __init__(self, provider, machines):
        self.infrastructure_provider = INFRASTRUCTURE_PROVIDERS_BY_NAME[provider]
        self.machines = machines

    def __call__(self):
        return self.infrastructure_provider(self.machines)