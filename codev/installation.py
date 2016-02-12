
from os import unlink
from .configuration import YAMLConfiguration

from .provider import BaseProvider


class BaseInstallation(object):
    def __init__(self, configuration):
        self._configuration = configuration


class ActualInstallation(BaseInstallation):
    def configuration(self, performer):
        YAMLConfiguration.from_configuration(self._configuration).save_to_file('tmp')
        performer.send_file('tmp', '.codev')
        unlink('tmp')
        return self._configuration


class Installation(BaseProvider):
    provider_class = BaseInstallation

Installation.register('actual', ActualInstallation)
