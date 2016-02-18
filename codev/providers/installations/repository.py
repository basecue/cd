from codev.installation import Installation, BaseInstallation


class RepositoryInstallation(BaseInstallation):
    def install(self, performer):
        performer.execute('apt-get install git -y --force-yes')
        performer.execute('git clone %s repository' % self.configuration.repository)
        return self.configuration

Installation.register('repository', RepositoryInstallation)
