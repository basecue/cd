from .provider import BaseProvider


class BaseInstallation(object):
    def __init__(self, options, *args, **kwargs):
        self.options = options
        super(BaseInstallation, self).__init__(*args, **kwargs)

    def configure(self, performer):
        raise NotImplementedError()


class Installation(BaseProvider):
    provider_class = BaseInstallation
