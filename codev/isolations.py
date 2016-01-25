class LXCIsolation(object):
    pass


ISOLATIONS = {
    'lxc': LXCIsolation
}


class Isolation(object):
    def __new__(cls, ident):
        return ISOLATIONS[ident]()
