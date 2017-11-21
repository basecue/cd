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

    def parse_option(self, option):
        if self.version and option != self.version:
            raise Exception("Version '{option}' is not allowed for git source.".format(option=option))


class GitSource(Source):
    provider_name = 'git'
    settings_class = GitSourceSettings

    def parse_version(self, executor):
        def find_branch(remote, branch):
            branches = executor.execute('git branch -r').splitlines()
            return '{remote}/{branch}'.format(remote=remote, branch=branch) in branches

        def find_tag(tag):
            return tag in executor.execute('git tag').splitlines()

        def find_commit(commit):
            return executor.check_execute('git log -F {commit} -n 1 --pretty=oneline'.format(commit=commit))

        version = self.option

        remotes = executor.execute('git remote').splitlines()

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
            self.repository_url = executor.execute('git remote get-url {remote}'.format(remote=remote))

        branch, tag, commit = None, None, None

        if not version:
            branch = executor.execute(
                'git branch -r --points-at {remote}/HEAD | grep -v HEAD'.format(remote=remote)
            )
            commit = None

        else:

            if find_branch(remote, version):
                branch = version
            elif find_tag(version):
                tag = version
            elif find_commit(version):
                commit = version
            else:
                raise ValueError("Branch, tag or commit '{version}' not found.".format(version=version))

        return branch, tag, commit

    def install(self, executor):
        branch, tag, commit = self.parse_version(executor)

        # TODO requirements
        # executor.install_packages('git')

        # obtain fingerprint from server and set .ssh/known_hosts properly

        # hostname = urlparse(self.repository_url).hostname

        # executor.execute('mkdir -p ~/.ssh')
        # ssh_line = executor.execute('ssh-keyscan -t rsa {hostname} 2> /dev/null'.format(hostname=hostname))
        # if not executor.check_execute('grep -qxF "{ssh_line}" ~/.ssh/known_hosts'.format(ssh_line=ssh_line)):
        #     executor.execute('echo "{ssh_line}" >> ~/.ssh/known_hosts'.format(ssh_line=ssh_line))

        # clone repository

        if branch:
            executor.execute('git clone {url} --branch {branch} --single-branch .'.format(
                url=self.repository_url,
                branch=branch
            ))
        elif commit:
            executor.execute('git init .')
            executor.execute('git remote add origin {url}'.format(url=self.repository_url))
            executor.execute('git fetch origin {commit}'.format(commit=commit))
            executor.execute('git reset --hard FETCH_HEAD')
        else:  # if self.tag
            executor.execute('git clone {url} .'.format(
                url=self.repository_url,
            ))
            executor.execute('git checkout {tag}'.format(
                url=self.repository_url,
                tag=tag
            ))

