from urllib.parse import urlparse

from git import Repo

from codev.core.executor import Command
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

    def install(self, executor):
        """
        Install project to directory

        :param executor:
        :type executor: codev.executor.Executor
        :return:
        """
        # TODO requirements
        # executor.install_packages('git')

        # obtain fingerprint from server and set .ssh/known_hosts properly

        # hostname = urlparse(self.repository_url).hostname

        # executor.execute('mkdir -p ~/.ssh')
        # ssh_line = executor.execute('ssh-keyscan -t rsa {hostname} 2> /dev/null'.format(hostname=hostname))
        # if not executor.check_execute('grep -qxF "{ssh_line}" ~/.ssh/known_hosts'.format(ssh_line=ssh_line)):
        #     executor.execute('echo "{ssh_line}" >> ~/.ssh/known_hosts'.format(ssh_line=ssh_line))

        # clean directory
        # if self.directory:
        #     if executor.exists_directory(self.directory):
        #         executor.check_execute('rm -rf {directory}'.format(directory=self.directory))

        # if self.directory:
        #     directory = self.directory
        # else:
        #     directory = '.'

        # clone repository
        if self.branch:
            executor.execute('git clone {url} --branch {object} --single-branch .'.format(
                url=self.repository_url,
                object=self.branch
            ))
        elif self.commit:
            executor.execute('git init .')
            executor.execute('git remote add origin {url}'.format(url=self.repository_url))
            executor.execute('git fetch origin {commit}'.format(commit=self.commit))
            executor.execute('git reset --hard FETCH_HEAD')
        else:  # if self.version
            executor.execute('git clone {url} .'.format(
                url=self.repository_url,
            ))
            executor.execute('git checkout {version}'.format(
                url=self.repository_url,
                version=self.version
            ))


class GitSource(Source):
    provider_name = 'git'

    def __init__(self, options, *args, **kwargs):
        if not options:
            # TODO if default, this message doesnt make any sense for user
            raise ValueError('Options must be specified.')

        self.git = Git(version=options, directory=self.directory)

        super().__init__(options, *args, **kwargs)

    def install(self, executor):
        self.git.install(executor)
