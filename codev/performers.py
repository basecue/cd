
class LocalPerformer(object):
    pass


class RemotePerformer(object):
    def __init__(self, ident):
        print('perform on %s' % ident)


class Performer(object):
    def __new__(cls, ident):
        if ident in ('local', 'localhost'):
            return LocalPerformer()
        else:
            return RemotePerformer(ident)


