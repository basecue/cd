from contextlib import contextmanager
from copy import copy

from codev.core.provider import Provider
from os import path

from codev.core.settings import HasSettings


class CommandError(Exception):
    def __init__(self, command, exit_code, error, output=None):
        self.command = command
        self.exit_code = exit_code
        self.error = error
        self.output = output

        super().__init__(
            "Command '{command}' failed with exit code '{exit_code}' with error:\n{error}".format(
                command=command, exit_code=exit_code, error=error
            )
        )


class Command(object):
    def __new__(cls, command_or_str, *args, **kwargs):
        if isinstance(command_or_str, Command):
            return command_or_str
        else:
            return super().__new__(cls)

    def __init__(self, command_str, logger=None, writein=None):
        self.command_str = command_str
        self.logger = logger
        self.writein = writein

    def __str__(self):
        return self.command_str

    def include(self):
        return self._copy(
            'bash -c "{command_str}"'.format(
                command_str=self.command_str.replace('\\', '\\\\').replace('$', '\$').replace('"', '\\"')
            )
        )

    def _copy(self, command_or_str):
        return self.__class__(command_or_str, logger=self.logger, writein=self.writein)

    def change_directory(self, directory):
        return self._copy('cd {directory} && {command_str}'.format(
            directory=directory,
            command_str=self.command_str
        ))

    def wrap(self, command_str):
        return self._copy(
            command_str.format(
                command=self.include()
            )
        )


class BaseExecutor(object):
    def execute_command(self, command):
        raise NotImplementedError()

    def send_file(self, source, target):
        raise NotImplementedError()

    @contextmanager
    def get_fo(self, remote_path):
        yield NotImplementedError()


class HasExecutor(object):
    def __init__(self, *args, executor, **kwargs):
        self.__executor = executor
        super().__init__(*args, **kwargs)

    @property
    def executor(self):
        return self.__executor


class ProxyExecutor(HasExecutor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._directories = []

    def check_execute(self, command_str, logger=None, writein=None):
        try:
            self.execute(command_str, logger=logger, writein=writein)
            return True
        except CommandError:
            return False    
    
    def execute(self, command_str, logger=None, writein=None):
        command = Command(command_str, logger=logger, writein=writein)
        for directory in reversed(self._directories):
            command = command.change_directory(directory)
        return self.execute_command(command)

    @property
    def inherited_executor(self):
        obj = copy(self)
        obj.__class__ = [base for base in self.__class__.__bases__ if issubclass(base, ProxyExecutor)][0]
        return obj

    def execute_command(self, command):
        return self.executor.execute_command(command)

    def send_file(self, source, target):
        return self.executor.send_file(source, target)

    @contextmanager
    def get_fo(self, remote_path):
        remote_path = path.join(*[directory for directory in reversed(self._directories)], remote_path)
        with self.executor.get_fo(remote_path) as fo:
            yield fo

    @contextmanager
    def change_directory(self, directory):
        self._directories.append(directory)
        yield
        self._directories.pop()

    def exists_directory(self, directory):
        return self.check_execute(
            '[ -d {directory} ]'.format(
                directory=directory
            )
        )

    def exists_file(self, filepath):
        return self.check_execute(
            '[ -f {filepath} ]'.format(
                filepath=filepath
            )
        )

    def create_directory(self, directory):
        self.execute('mkdir -p {directory}'.format(directory=directory))


class Executor(Provider, HasSettings, BaseExecutor):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
        # TODO move to future authentication module
        # if not self.check_execute('ssh-add -L'):
        #     raise CommandError("No SSH identities found, use the 'ssh-add'.")

    pass

"""
background runner
"""

from collections import namedtuple
from time import sleep
from logging import getLogger

Isolation = namedtuple(
    'Isolation', ['output_file', 'error_file', 'exitcode_file', 'command_file', 'pid_file', 'temp_file']
)

OUTPUT_FILE = 'codev.out'
ERROR_FILE = 'codev.err'
EXITCODE_FILE = 'codev.exit'
COMMAND_FILE = 'codev.command'
PID_FILE = 'codev.pid'
TEMP_FILE = 'codev.temp'

from time import time


class BackgroundExecutor(Executor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._isolation_cache = None
        self.__isolation_directory = None
        self.logger = getLogger(__name__)
        self.ident = kwargs.pop('ident', str(time()))

    @property
    def _isolation_directory(self):
        if not self.__isolation_directory:
            # if not self.ident:
            #     ssh_info = self.executor.execute('echo $SSH_CLIENT')
            #     ip, remote_port, local_port = ssh_info.split()
            #     self.ident = 'control_{ip}_{remote_port}_{local_port}'.format(
            #         ip=ip, remote_port=remote_port, local_port=local_port
            #     )

            self.__isolation_directory = '/tmp/.codev/{ident}'.format(
                ident=self.ident
            )

        return self.__isolation_directory

    def _create_isolation(self):
        self.executor.execute('mkdir -p %s' % self._isolation_directory)

        output_file, error_file, exitcode_file, command_file, pid_file, temp_file = map(
            lambda f: '%s/%s' % (self._isolation_directory, f),
            [OUTPUT_FILE, ERROR_FILE, EXITCODE_FILE, COMMAND_FILE, PID_FILE, TEMP_FILE]
        )

        return Isolation(
            command_file=command_file,
            output_file=output_file,
            error_file=error_file,
            exitcode_file=exitcode_file,
            pid_file=pid_file,
            temp_file=temp_file
        )

    @property
    def _isolation(self):
        if not self._isolation_cache:
            self._isolation_cache = self._create_isolation()
        return self._isolation_cache

    def _clean(self):
        self.executor.execute('rm -rf %s' % self._isolation_directory)

    def _file_exists(self, filepath):
        return self.executor.check_execute('[ -f %s ]' % filepath)

    def _bg_check(self, pid):
        return self.executor.check_execute('ps -p %s -o pid=' % pid)

    def _bg_log(self, logger, skip_lines):
        output = self.executor.execute('tail {output_file} -n+{skip_lines}'.format(
            output_file=self._isolation.output_file,
            skip_lines=skip_lines)
        )
        if not output:
            return 0

        output_lines = output.splitlines()

        for line in output_lines:
            (logger or self.output_logger).debug(line)
        return len(output_lines)

    def _bg_stop(self, pid):
        return self._bg_signal(pid)

    def _bg_kill(self, pid):
        self._bg_signal(pid, 9)
        self._clean()

    def _bg_signal(self, pid, signal=None):
        return self.executor.execute(
            'pkill {signal}-P {pid}'.format(
                pid=pid,
                signal='-%s ' % signal if signal else ''
            )
        )

    def _bg_wait(self, pid, logger=None):
        skip_lines = 1
        while self._bg_check(pid):
            skip_lines += self._bg_log(logger, skip_lines)
            sleep(0.25)

        self._bg_log(logger, skip_lines)

    def _cat_file(self, catfile):
        return self.executor.execute('cat %s' % catfile)

    def _get_bg_running_pid(self):
        return self._cat_file(self._isolation.pid_file)

    def execute(self, command, logger=None, writein=None, wait=True):
        self.logger.debug('Command: {command} wait: {wait}'.format(command=command, wait=wait))
        isolation = self._isolation

        if self._file_exists(isolation.exitcode_file) and self._cat_file(isolation.exitcode_file) == '':
            if self._file_exists(isolation.pid_file):
                pid = self._cat_file(isolation.pid_file)
                if pid and self._bg_check(pid):
                    raise CommandError('Another process is running.')

        self.executor.execute('echo "" > {output_file} > {error_file} > {exitcode_file} > {pid_file}'.format(
            **isolation._asdict()
        ))

        self.executor.execute(
            'tee {command_file} > /dev/null && chmod +x {command_file}'.format(
                **isolation._asdict()
            ),
            writein='{command}; echo $? > {exitcode_file}\n'.format(
                command=command,
                exitcode_file=isolation.exitcode_file
            )
        )

        bg_command = 'bash -c "nohup {command_file} > {output_file} 2> {error_file} & echo \$! | tee {pid_file}"'.format(
            **isolation._asdict()
        )

        # max lines against readline hang
        pid = self.executor.execute(bg_command, writein=writein)

        if not pid.isdigit():
            raise ValueError('not a pid %s' % pid)

        if not wait:
            return self.ident

        self._bg_wait(pid, logger=logger)

        exit_code = int(self._cat_file(isolation.exitcode_file))

        output = self._cat_file(isolation.output_file)

        if exit_code:
            err = self._cat_file(isolation.error_file)
            self._clean()
            raise CommandError(command, exit_code, err, output)

        self._clean()
        return output

    def _control(self, method, *args, **kwargs):
        """
        :param method:
        :param args:
        :param kwargs:
        :return:
        """
        self.logger.debug('control command: {method}'.format(method=method.__name__))
        try:
            pid = self._get_bg_running_pid()
        except CommandError as e:
            raise CommandError('No active process.')

        if pid:
            try:
                method(pid, *args, **kwargs)
                return True
            except CommandError as e:
                return False
        else:
            return False

    def join(self, logger=None):
        return self._control(self._bg_wait, logger=logger)

    def stop(self):
        return self._control(self._bg_stop)

    def kill(self):
        return self._control(self._bg_kill)


"""
Output reader
"""
from multiprocessing.pool import ThreadPool


class OutputReader(object):
    thread_pool = ThreadPool(processes=2)

    def __init__(self, stdout, stderr, logger=None):
        self._stdout_output = []
        self._stderr_output = []

        self.terminated = False

        self._stdout_reader = self.thread_pool.apply_async(
            self._reader,
            args=(stdout,),
            kwds=dict(logger=logger)
        )

        self._stderr_reader = self.thread_pool.apply_async(
            self._reader,
            args=(stderr,)
        )

    def _reader(self, output, logger=None):
        output_lines = []
        while True:
            try:
                if self.terminated:
                    output.flush()

                lines = output.readlines()
            except ValueError:  # closed file
                break

            if not lines:
                if self.terminated:
                    break

                sleep(0.1)
                continue

            for line in lines:
                output_line = line.decode('utf-8').rstrip('\n')
                output_lines.append(output_line)
                if logger:
                    logger.debug(output_line)

        return '\n'.join(output_lines)

    def output(self):
        self.terminated = True
        return self._stdout_reader.get(), self._stderr_reader.get()



