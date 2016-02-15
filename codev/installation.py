from .provider import BaseProvider


class BaseInstallation(object):
    def __init__(self, configuration):
        self._configuration = configuration

    def configuration(self, performer):
        raise NotImplementedError()


class Installation(BaseProvider):
    provider_class = BaseInstallation
