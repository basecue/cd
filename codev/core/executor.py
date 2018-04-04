from typing import Type, Union, IO, Optional, Any, List, Iterator

from contextlib import contextmanager
import os.path
from logging import Logger

from codev.core.provider import Provider

from codev.core.settings import HasSettings


class Command(object):
    def __new__(cls, command_or_str: Union['Command', str], *args: Any, **kwargs: Any) -> 'Command':
        if isinstance(command_or_str, Command):
            return command_or_str
        else:
            return super().__new__(cls)

    def __init__(self, command_str: str, output_logger: Optional[Logger] = None, writein: Optional[str] = None) -> None:
        self.command_str = command_str
        self.output_logger = output_logger
        self.writein = writein

    def __str__(self) -> str:
        return self.command_str

    def escape(self) -> 'Command':
        return self._copy(self.command_str.replace('\\', '\\\\').replace('$', '\$').replace('"', '\\"'))

    def include(self) -> 'Command':
        return self._copy(
            'bash -c "{command}"'.format(
                command=self.escape()
            )
        )

    def _copy(self, command_or_str: Union['Command', str]) -> 'Command':
        return self.__class__(command_or_str, output_logger=self.output_logger, writein=self.writein)

    def change_directory(self, directory: str) -> 'Command':
        return self._copy(f'cd {directory} && {self.command_str}')

    def wrap(self, command_str: str) -> 'Command':
        return self._copy(
            command_str.format(
                command=self.include()
            )
        )

    def wrap_escape(self, command_str: str) -> 'Command':
        return self._copy(
            command_str.format(
                command=self.include().escape()
            )
        )

    # def light_wrap_escape(self, command_str):
    #     return self._copy(
    #         command_str.format(
    #             command=self.escape()
    #         )
    #     )


class CommandError(Exception):
    def __init__(self, command: Command, exit_code: int, error: str, output: Optional[str] = None) -> None:
        self.command = command
        self.exit_code = exit_code
        self.error = error
        self.output = output

        super().__init__(
            f"Command '{command}' failed with exit code '{exit_code}' with error:\n{error}"
        )


class BareExecutor(object):
    def execute_command(self, command: Command) -> str:
        raise NotImplementedError()

    @contextmanager
    def open_file(self, remote_path: str) -> Iterator[IO]:
        raise NotImplementedError()

    def send_file(self, source: str, target: str) -> None:
        raise NotImplementedError()

    def check_execute(
            self,
            command_str: str,
            output_logger: Optional[Logger] = None,
            writein: Optional[str] = None
    ) -> bool:
        try:
            self.execute(command_str, output_logger=output_logger, writein=writein)
            return True
        except CommandError:
            return False

    def execute(self, command_str: str, output_logger: Optional[Logger] = None, writein: Optional[str] = None) -> str:
        command = Command(command_str, output_logger=output_logger, writein=writein)

        command = self.process_command(command)

        return self.execute_command(command)

    def process_command(self, command: Command) -> Command:
        return command


class HasExecutor(object):
    def __init__(self, *args: Any, executor: BareExecutor, **kwargs: Any) -> None:
        self.executor = executor
        super().__init__(*args, **kwargs)


class BareProxyExecutor(HasExecutor, BareExecutor):
    executor_class: Type[HasExecutor] = None
    executor_class_pass_kwargs: List[str] = []

    def __init__(self, executor: BareExecutor, **kwargs: Any) -> None:
        if self.executor_class:
            executor_kwargs = {key: kwargs.get(key) for key in self.executor_class_pass_kwargs}
            executor = self.executor_class(executor=executor, **executor_kwargs)

        super().__init__(executor=executor, **kwargs)

    @property
    def effective_executor(self) -> BareExecutor:
        return self.executor

    def execute_command(self, command: Command) -> str:
        return self.effective_executor.execute_command(command)

    @contextmanager
    def open_file(self, remote_path: str) -> Iterator[IO]:
        with self.effective_executor.open_file(remote_path) as fo:
            yield fo

    def send_file(self, source: str, target: str) -> None:
        # logger.debug("Send file: '{source}' '{target}'".format(source=source, target=target))
        self.effective_executor.send_file(source, target)


class BaseProxyExecutor(BareProxyExecutor):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.directories: List[str] = []

    def send_file(self, source: str, target: str) -> None:
        # logger.debug("Send file: '{source}' '{target}'".format(source=source, target=target))
        expanduser_source = os.path.expanduser(source)
        super().send_file(expanduser_source, target)

    @contextmanager
    def open_file(self, remote_path: str) -> Iterator[IO]:
        remote_path = os.path.join(*[directory for directory in reversed(self.directories)], remote_path)
        with super().open_file(remote_path) as fo:
            yield fo

    def exists_directory(self, directory: str) -> bool:
        return self.check_execute(
            f'[ -d {directory} ]'
        )

    def exists_file(self, filepath: str) -> bool:
        return self.check_execute(
            f'[ -f {filepath} ]'
        )

    def create_directory(self, directory: str) -> None:
        self.execute(f'mkdir -p {directory}')

    def delete_path(self, _path: str) -> None:
        self.execute(f'rm -rf {_path}')

    @contextmanager
    def change_directory(self, directory: str) -> Iterator[None]:
        assert directory
        self.directories.append(directory)
        yield
        self.directories.pop()

    def process_command(self, command: Command) -> Command:
        for directory in reversed(self.directories):
            command = command.change_directory(directory)
        return command


class ProxyExecutor(BaseProxyExecutor):
    executor_class = BaseProxyExecutor


class Executor(Provider, HasSettings, BareExecutor):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    # TODO move to future authentication module
    # if not self.check_execute('ssh-add -L'):
    #     raise CommandError("No SSH identities found, use the 'ssh-add'.")

    pass
