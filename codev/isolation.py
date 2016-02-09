from .provider import BaseProvider


class BaseIsolationProvider(object):
    def __init__(self, performer):
        self.performer = performer


class IsolationProvider(BaseProvider):
    provider_class = BaseIsolationProvider
