
class LXCInfrastructure(object):
    pass


PROVISIONS = {
    'lxc': LXCInfrastructure

}


class InfrastructureProvision(object):
    def __new__(cls, ident):
        return PROVISIONS[ident]()