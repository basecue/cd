from codev.isolator import BaseIsolator, Isolator


class NoneIsolator(BaseIsolator):
    def exists(self):
        return True


Isolator.register('none', NoneIsolator)
