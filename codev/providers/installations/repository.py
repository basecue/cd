from codev.installation import Installation, BaseInstallation
from codev.configuration import BaseConfiguration
from git import Repo


class RepositoryConfiguration(BaseConfiguration):
    @property
    def url(self):
        return self.data['url']


class RepositoryInstallation(BaseInstallation):
    configuration_class = RepositoryConfiguration

    def __init__(self, *args, **kwargs):
        self.branch = None
        self.tag = None
        self.commit = None
        super(RepositoryInstallation, self).__init__(*args, **kwargs)

    def process_options(self, options):
        if not options:
            raise ValueError('Repository options must be specified.')
        repo = Repo()

        remote = repo.remote()
        remote.fetch()

        # branch
        if options in remote.refs:
            self.branch = options
            return

        # tag
        if options in repo.tags:
            self.tag = options
            return

        # commit
        for commit in repo.iter_commits():
            if options == commit:
                self.commit = commit
                return

        raise ValueError(options)

    @property
    def id(self):
        return self.branch or self.tag or self.commit

    def install(self, performer, directory):
        """
        Install project to directory

        :param performer:
        :param directory:
        :return:
        """
        performer.execute('apt-get install git -y --force-yes')

        # TODO checking fingerprints instead of copying known_hosts
        # http://serverfault.com/questions/132970/can-i-automatically-add-a-new-host-to-known-hosts
        # http://serverfault.com/questions/447028/non-interactive-git-clone-ssh-fingerprint-prompt
        # http://unix.stackexchange.com/questions/94448/how-to-add-an-ip-range-to-known-hosts
        # https://help.github.com/articles/what-are-github-s-ssh-key-fingerprints/
        # ssh-keyscan -t rsa,dsa github.com 2> /dev/null > /tmp/key && ssh-keygen -lf /tmp/key
        # ssh-keygen -H -F github.com
        # github.com,192.30.252.*,192.30.253.*,192.30.254.*,192.30.255.* ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAq2A7hRGmdnm9tUDbO9IDSwBK6TbQa+PXYPCPy6rbTrTtw7PHkccKrpp0yVhp5HdEIcKr6pLlVDBfOLX9QUsyCOV0wzfjIJNlGEYsdlLJizHhbn2mUjvSAHQqZETYP81eFzLQNnPHt4EVVUh7VfDESU84KezmD5QlWpXLmvU31/yMf+Se8xhHTvKSCZIFImWwoG6mbUoWf9nzpIoaSjB+weqqUUmpaaasXVal72J+UX2B+2RPW3RcT0eOzQgqlJL3RKrTJvdsjE3JEAvGq3lGHSZXy28G3skua2SmVi/w4yCE6gbODqnTWlg7+wC604ydGXA8VJiS5ap43JXiUFFAaQ==

        performer.execute('mkdir -p ~/.ssh')
        performer.send_file('~/.ssh/known_hosts', '~/.ssh/known_hosts')

        if performer.check_execute('[ -d {directory} ]'.format(directory=directory)):
            performer.check_execute('rm -rf {directory}'.format(directory=directory))

        if self.branch or self.tag:
            performer.execute('git clone {url} --branch {object} --single-branch {directory}'.format(
                url=self.configuration.url,
                directory=directory,
                object=self.branch or self.tag
            ))
        elif self.commit:
            # TODO TEST - cd
            performer.execute('git init {directory}'.format(directory=directory))
            performer.execute('cd {directory}'.format(directory=directory))
            performer.execute('git remote add origin {url}'.format(url=self.configuration.url))
            performer.execute('git fetch origin {commit}'.format(commit=self.commit))
            performer.execute('git reset --hard FETCH_HEAD')

        return directory

Installation.register('repository', RepositoryInstallation)
