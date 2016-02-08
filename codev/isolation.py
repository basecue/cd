from .provider import BaseProvider


class BaseIsolationProvider(object):
    def __init__(self, performer, ident):
        self.performer = performer
        self.ident = ident


class IsolationProvider(BaseProvider):
    provider_class = BaseIsolationProvider
