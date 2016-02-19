from codev.installation import Installation, BaseInstallation


class RepositoryInstallation(BaseInstallation):
    def install(self, performer):
        performer.execute('apt-get install git -y --force-yes')

        #TODO fingerprints
        # http://serverfault.com/questions/132970/can-i-automatically-add-a-new-host-to-known-hosts
        # http://serverfault.com/questions/447028/non-interactive-git-clone-ssh-fingerprint-prompt

        performer.execute('git clone %s repository' % self.configuration.repository)
        return self.configuration

Installation.register('repository', RepositoryInstallation)
