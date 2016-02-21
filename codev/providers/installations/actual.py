from os import unlink

from codev.configuration import YAMLConfigurationWriter
from codev.installation import Installation, BaseInstallation


class ActualInstallation(BaseInstallation):
    def configure(self, performer):
        YAMLConfigurationWriter(self.configuration).save_to_file('tmp')
        performer.send_file('tmp', '.codev')
        unlink('tmp')
        return self.configuration.version


Installation.register('actual', ActualInstallation)
