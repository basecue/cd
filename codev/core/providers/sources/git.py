from urllib.parse import urlparse

from git import Repo

from codev.core.source import Source


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

        # obtain fingerprint from server and set .ssh/known_hosts properly
        hostname = urlparse(self.repository_url).hostname

        performer.execute('mkdir -p ~/.ssh')
        ssh_line = performer.execute('ssh-keyscan -t rsa {hostname} 2> /dev/null'.format(hostname=hostname))
        if not performer.check_execute('grep -qxF "{ssh_line}" ~/.ssh/known_hosts'.format(ssh_line=ssh_line)):
            performer.execute('echo "{ssh_line}" >> ~/.ssh/known_hosts'.format(ssh_line=ssh_line))

        # clean directory
        if self.directory:
            if performer.check_execute('[ -d {directory} ]'.format(directory=self.directory)):
                performer.check_execute('rm -rf {directory}'.format(directory=self.directory))

        if self.directory:
            directory = self.directory
        else:
            directory = '.'

        # clone repository
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
