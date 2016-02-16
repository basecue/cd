from os import unlink

from codev.configuration import YAMLConfiguration
from codev.installation import Installation, BaseInstallation


class RepositoryInstallation(BaseInstallation):
    def install(self, performer):
        performer.execute('git clone %s' % self.configuration.repository)
        performer.get_file(self.configuration.repository)
        YAMLConfiguration.from_configuration(self.configuration).save_to_file('tmp')
        performer.send_file('tmp', '.codev')
        unlink('tmp')
        return self.configuration

Installation.register('repository', RepositoryInstallation)
