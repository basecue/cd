from codev.isolator import BaseIsolator, Isolator


class NoneIsolator(BaseIsolator):
    pass

Isolator.register('none', NoneIsolator)
