
class LXCInfrastructureProvision(object):
    def __init__(self, configuration):
        self.performer = LocalPerformer()
        self.configuration = configuration


PROVISIONS = {
    'lxc': LXCInfrastructureProvision
}


class InfrastructureProvision(object):
    def __new__(cls, ident):
        return PROVISIONS[ident]