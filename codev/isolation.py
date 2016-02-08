from .provider import BaseProvider


class BaseIsolationProvider(object):
    def __init__(self, ident):
        self.ident = ident


class IsolationProvider(BaseProvider):
    provider_class = BaseIsolationProvider
