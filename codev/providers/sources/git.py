from codev.source import Source
from git import Repo


class Git(object):
    def __init__(self, version=None, repository_url=None, directory=None):

        self.directory = directory
        self.version = None
        self.branch, self.commit = None, None

        if not repository_url:
            self.repository = Repo()
            self.branch, self.commit = self._branch_or_commit(version)
            self.repository_url = self.repository.remotes.origin.url
        else:
            self.repository_url = repository_url
            self.version = version

    def _branch_or_commit(self, version):
        remote = self.repository.remote()
        remote.fetch()

        # branch or tag
        if version in remote.refs or version in self.repository.tags:
            return version, None

        # commit
        else:
            for commit in self.repository.iter_commits():
                if version == commit:
                    return None, commit
            else:
                raise ValueError("Branch, tag or commit '{version}' not found.".format(version=version))

    def install(self, performer):
        """
        Install project to directory

        :param performer:
        :type performer: codev.performer.BasePerformer
        :return:
        """
        # TODO requirements
        # performer.install_packages('git')

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

        if self.directory:
            if performer.check_execute('[ -d {directory} ]'.format(directory=self.directory)):
                performer.check_execute('rm -rf {directory}'.format(directory=self.directory))

        if self.directory:
            directory = self.directory
        else:
            directory = '.'

        if self.branch:
            performer.execute('git clone {url} --branch {object} --single-branch {directory}'.format(
                url=self.repository_url,
                directory=directory,
                object=self.branch
            ))
        elif self.commit:
            performer.execute('git init {directory}'.format(directory=directory))
            with performer.change_directory(directory):
                performer.execute('git remote add origin {url}'.format(url=self.repository_url))
                performer.execute('git fetch origin {commit}'.format(commit=self.commit))
                performer.execute('git reset --hard FETCH_HEAD')
        else:  # if self.version
            performer.execute('git clone {url} {directory}'.format(
                url=self.repository_url,
                directory=directory
            ))
            with performer.change_directory(directory):
                performer.execute('git checkout {version}'.format(
                    url=self.repository_url,
                    version=self.version
                ))


class GitSource(Source):
    provider_name = 'git'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.git = Git(version=self.options, directory=self.directory)

    def process_options(self, options):
        if not options:
            raise ValueError('Repository options must be specified.')

        return options

    def install(self, performer):
        self.git.install(performer)
