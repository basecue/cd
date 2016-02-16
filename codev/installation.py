from .provider import BaseProvider


class BaseInstallation(object):
    def __init__(self, configuration):
        self.configuration = configuration

    def install(self, performer):
        raise NotImplementedError()


class Installation(BaseProvider):
    provider_class = BaseInstallation
