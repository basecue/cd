from .. import AnsibleSource
from codev.settings import BaseSettings
from ....sources.git import Git


class AnsibleGitSourceSettings(BaseSettings):
    @property
    def url(self):
        return self.data.get('url')

    @property
    def version(self):
        return self.data.get('version', '')

    @property
    def commit(self):
        return self.data.get('commit', '')


class AnsibleGitSource(Git, AnsibleSource):
    provider_name = 'git'
    settings_class = AnsibleGitSourceSettings

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            version=self.settings.version,
            commit=self.settings.commit,
            repository_url=self.settings.url,
            directory='/tmp/ansible_git',
            **kwargs
        )
