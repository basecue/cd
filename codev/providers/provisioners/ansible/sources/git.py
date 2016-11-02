from ..source import AnsibleSource
from codev.settings import BaseSettings
from ....sources.git import Git


class AnsibleGitSourceSettings(BaseSettings):
    @property
    def url(self):
        return self.data.get('url')

    @property
    def version(self):
        return self.data.get('version', 'master')

    @property
    def commit(self):
        return self.data.get('commit', '')


class AnsibleGitSource(AnsibleSource):
    provider_name = 'git'
    settings_class = AnsibleGitSourceSettings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.git = Git(
            version=self.settings.version,
            commit=self.settings.commit,
            repository_url=self.settings.url,
            directory='/tmp/ansible_git'
        )

    def install(self):
        self.git.install(self.performer)

    @property
    def directory(self):
        return self.git.directory
