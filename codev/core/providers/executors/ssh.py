from typing import IO

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

    @property
    def options(self):
        return self.data.get('options', {})

    # @property
    # def password(self):
    #     return self.data.get('password', None)


class SSHExecutor(LocalExecutor):
    provider_name = 'ssh'
    settings_class = SSHExecutorSettings

    def _format_options(self):
        return ' '.join([
            f'-o {key}={value}' for key, value in self.settings.options.items()
        ])

    def execute_command(self, command: Command):
        command = command.wrap_escape('ssh -A {username}@{hostname} -p {port} {options} -- "{{command}}"'.format(
                username=self.settings.username,
                hostname=self.settings.hostname,
                port=self.settings.port,
                options=self._format_options()
            )
        )
        return super().execute_command(command)

    def _scp_base(self) -> str:
        return 'scp -p {port} {options}'.format(
            port=self.settings.port,
            options=self._format_options(),
        )

    def send_file(self, source: str, target: str) -> None:
        command = Command('{scp_base} {source} {username}@{hostname}:{target}'.format(
            scp_base=self._scp_base(),
            username=self.settings.username,
            hostname=self.settings.hostname,
            source=source,
            target=target
        ))

        super().execute_command(command)

    def open_file(self, remote_path: str) -> IO:
        with NamedTemporaryFile() as fo:
            command = Command(
                '{scp_base} {username}@{hostname}:{remote_path} {target} '.format(
                    scp_base=self._scp_base(),
                    username=self.settings.username,
                    hostname=self.settings.hostname,
                    port=self.settings.port,
                    remote_path=remote_path,
                    target=fo.name
                )
            )
            super().execute_command(command)
            yield fo

