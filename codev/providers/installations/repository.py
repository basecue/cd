from codev.installation import Installation, BaseInstallation


class RepositoryInstallation(BaseInstallation):
    def install(self, performer):
        performer.execute('git clone %s' % self.configuration.repository)
        return self.configuration

Installation.register('repository', RepositoryInstallation)
