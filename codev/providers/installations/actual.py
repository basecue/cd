from os import unlink

from codev.configuration import YAMLConfiguration
from codev.installation import Installation, BaseInstallation


class ActualInstallation(BaseInstallation):
    def configuration(self, performer):
        YAMLConfiguration.from_configuration(self._configuration).save_to_file('tmp')
        performer.send_file('tmp', '.codev')
        unlink('tmp')
        return self._configuration

Installation.register('actual', ActualInstallation)
