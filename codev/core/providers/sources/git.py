from typing import Optional, Tuple, Any

from codev.core.executor import BareExecutor
from codev.core.settings import BaseSettings
from codev.core.source import Source


class GitSourceSettings(BaseSettings):
    @property
    def url(self) -> Optional[str]:
        return self.data.get('url')

    @property
    def remote(self) -> Optional[str]:
        return self.data.get('remote')

    @property
    def version(self) -> Optional[str]:
        return self.data.get('version')


class GitSource(Source):
    provider_name = 'git'
    settings_class = GitSourceSettings

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        if self.settings.version and self.option != self.settings.version:
            raise Exception(f"Version '{self.option}' is not allowed for git source.")

    def parse_version(self, executor: BareExecutor) -> Tuple[str, str, str, str]:
        def find_branch(remote: str, branch: str) -> bool:
            branches = executor.execute('git branch -r').splitlines()
            return f'{remote}/{branch}' in branches

        def find_tag(tag: str) -> bool:
            return tag in executor.execute('git tag').splitlines()

        def find_commit(commit: str) -> bool:
            return executor.check_execute(f'git log -F {commit} -n 1 --pretty=oneline')

        version = self.option

        remotes = executor.execute('git remote').splitlines()

        if self.settings.remote:
            remote = self.settings.remote
            if remote not in remotes:
                raise ValueError(f"Remote '{remote}' is not found.")
        else:
            if 'origin' in remotes:
                remote = 'origin'
            else:
                remote = remotes[0]

        if self.settings.url:
            repository_url = self.settings.url
        else:
            repository_url = executor.execute(f'git remote get-url {remote}')

        branch, tag, commit = None, None, None

        if not version:
            branch = executor.execute(
                f'git branch -r --points-at {remote}/HEAD | grep -v HEAD'
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
                raise ValueError(f"Branch, tag or commit '{version}' not found.")

        return repository_url, branch, tag, commit

    def install(self, executor: BareExecutor) -> None:
        repository_url, branch, tag, commit = self.parse_version(executor)

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
            executor.execute(f'git clone {repository_url} --branch {branch} --single-branch .')
        elif commit:
            executor.execute('git init .')
            executor.execute(f'git remote add origin {repository_url}')
            executor.execute(f'git fetch origin {commit}')
            executor.execute('git reset --hard FETCH_HEAD')
        else:  # if tag
            executor.execute(f'git clone {repository_url} .')
            executor.execute(f'git checkout {tag}')
