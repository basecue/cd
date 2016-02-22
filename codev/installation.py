from .provider import BaseProvider


class BaseInstallation(object):
    def __init__(self, options):
        self.options = options

    def configure(self, performer):
        raise NotImplementedError()


class Installation(BaseProvider):
    provider_class = BaseInstallation
