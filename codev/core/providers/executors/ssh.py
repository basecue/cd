from codev.core.executor import Command
from .local import LocalExecutor
from codev.core.settings import BaseSettings
from tempfile import NamedTemporaryFile


class SSHExecutorSettings(BaseSettings):
    @property
    def hostname(self):
        return self.data.get('hostname', 'localhost')

    @property
    def port(self):
        return self.data.get('port', 22)

    @property
    def username(self):
        return self.data.get('username', None)

    # @property
    # def password(self):
    #     return self.data.get('password', None)


class SSHExecutor(LocalExecutor):
    provider_name = 'ssh'
    settings_class = SSHExecutorSettings

    def execute_command(self, command):
        command = command.wrap_escape('ssh -A {username}@{hostname} -p {port} -- "{{command}}"'.format(
                username=self.settings.username,
                hostname=self.settings.hostname,
                port=self.settings.port
            )
        )
        return super().execute_command(command)

    def send_file(self, source, target):
        command = Command('scp -p {port} {source} {username}@{hostname}:{target}'.format(
            username=self.settings.username,
            hostname=self.settings.hostname,
            port=self.settings.port,
            source=source,
            target=target
        ))

        super().execute_command(command)

    def open_file(self, remote_path):
        with NamedTemporaryFile() as fo:
            command = Command(
                'scp -p {port} {username}@{hostname}:{remote_path} {target} '.format(
                    username=self.settings.username,
                    hostname=self.settings.hostname,
                    port=self.settings.port,
                    remote_path=remote_path,
                    target=fo.name
                )
            )
            super().execute_command(command)
            yield fo

