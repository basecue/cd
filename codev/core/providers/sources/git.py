from codev.core.settings import BaseSettings
from codev.core.source import Source


class GitSourceSettings(BaseSettings):
    @property
    def url(self):
        return self.data.get('url')

    def remote(self):
        return self.data.get('remote')

    @property
    def version(self):
        return self.data.get('version')


class GitSource(Source):
    provider_name = 'git'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        remotes = self.executor.execute('git remote').splitlines()

        if self.settings.remote:
            if self.settings.remote not in remotes:
                raise ValueError("Remote '{remote}' is not found.")
        else:
            if 'origin' in remotes:
                remote = 'origin'
            else:
                remote = remotes[0]

        if self.settings.url:
            self.repository_url = self.settings.url
        else:
            self.repository_url = self.executor.execute('git remote get-url {remote}'.format(remote=remote))

        self.branch, self.tag, self.commit = None, None, None

        if not self.settings.version:
            self.branch = self.executor.execute(
                'git branch -r --points-at {remote}/HEAD | grep -v HEAD'.format(remote=remote)
            )
            self.commit = None

        else:
            version = self.settings.version
            if self.find_branch(remote, version):
                self.branch = version
            elif self.find_tag(version):
                self.tag = version
            elif self.find_commit(version):
                self.commit = version
            else:
                raise ValueError("Branch, tag or commit '{version}' not found.".format(version=version))

    def find_branch(self, remote, branch):
        branches = self.executor.execute('git branch -r').splitlines()
        return '{remote}/{branch}'.format(remote=remote, branch=branch) in branches

    def find_tag(self, tag):
        return tag in self.executor.execute('git tag').splitlines()

    def find_commit(self, commit):
        return self.executor.check_execute('git log -F {commit} -n 1 --pretty=oneline'.format(commit=commit))

    def install(self):
        # TODO requirements
        # executor.install_packages('git')

        # obtain fingerprint from server and set .ssh/known_hosts properly

        # hostname = urlparse(self.repository_url).hostname

        # executor.execute('mkdir -p ~/.ssh')
        # ssh_line = executor.execute('ssh-keyscan -t rsa {hostname} 2> /dev/null'.format(hostname=hostname))
        # if not executor.check_execute('grep -qxF "{ssh_line}" ~/.ssh/known_hosts'.format(ssh_line=ssh_line)):
        #     executor.execute('echo "{ssh_line}" >> ~/.ssh/known_hosts'.format(ssh_line=ssh_line))

        # clone repository
        if self.branch:
            self.executor.execute('git clone {url} --branch {branch} --single-branch .'.format(
                url=self.repository_url,
                branch=self.branch
            ))
        elif self.commit:
            self.executor.execute('git init .')
            self.executor.execute('git remote add origin {url}'.format(url=self.repository_url))
            self.executor.execute('git fetch origin {commit}'.format(commit=self.commit))
            self.executor.execute('git reset --hard FETCH_HEAD')
        else:  # if self.tag
            self.executor.execute('git clone {url} .'.format(
                url=self.repository_url,
            ))
            self.executor.execute('git checkout {tag}'.format(
                url=self.repository_url,
                tag=self.tag
            ))

