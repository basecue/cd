from os import unlink

from codev.configuration import YAMLConfiguration
from codev.installation import Installation, BaseInstallation


class SvcInstallation(BaseInstallation):
    def configuration(self, performer):
        performer.execute('git clone %s' % self._configuration.repository)
        performer.get_file(self._configuration.repository)
        YAMLConfiguration.from_configuration(self._configuration).save_to_file('tmp')
        performer.send_file('tmp', '.codev')
        unlink('tmp')
        return self._configuration

Installation.register('svc', SvcInstallation)
