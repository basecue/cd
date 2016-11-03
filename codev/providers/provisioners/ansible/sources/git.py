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


class AnsibleGitSource(AnsibleSource):
    provider_name = 'git'
    settings_class = AnsibleGitSourceSettings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.git = Git(
            version=self.settings.version,
            repository_url=self.settings.url,
            directory=self.directory
        )

    def install(self):
        self.git.install(self.performer)

    @property
    def directory(self):
        return '/tmp/ansible_git'
