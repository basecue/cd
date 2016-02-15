from .provider import BaseProvider


class BaseInstallation(object):
    def __init__(self, configuration):
        self._configuration = configuration


class Installation(BaseProvider):
    provider_class = BaseInstallation
