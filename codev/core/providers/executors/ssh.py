from typing import IO, Optional, Dict, Iterator

import contextlib
import tempfile

from codev.core.executor import Command
from codev.core.settings import BaseSettings

from .local import LocalExecutor


class SSHExecutorSettings(BaseSettings):
    @property
    def hostname(self) -> str:
        return self.data.get('hostname', 'localhost')

    @property
    def port(self) -> int:
        return self.data.get('port', 22)

    @property
    def username(self) -> Optional[str]:
        return self.data.get('username')

    @property
    def options(self) -> Dict[str, str]:
        return self.data.get('options', {})

    # @property
    # def password(self):
    #     return self.data.get('password', None)


class SSHExecutor(LocalExecutor):
    provider_name = 'ssh'
    settings_class = SSHExecutorSettings

    def _format_options(self) -> str:
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

    @contextlib.contextmanager
    def open_file(self, remote_path: str) -> Iterator[IO]:
        with tempfile.NamedTemporaryFile() as fo:
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

