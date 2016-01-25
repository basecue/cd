
class LXCInfrastructureProvision(object):
    pass


PROVISIONS = {
    'lxc': LXCInfrastructureProvision
}


class InfrastructureProvision(object):
    def __new__(cls, ident):
        return PROVISIONS[ident]()