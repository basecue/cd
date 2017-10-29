from contextlib import contextmanager
from functools import wraps

from codev.core.performer import HasPerformer, CommandError


class Command(object):
    def __init__(self, command):
        self.command = command

    def __str__(self):
        return self.command

    def _include_command(self, command):
        return command.replace('\\', '\\\\').replace('$', '\$').replace('"', '\\"')

    def change_directory(self, directory):
        return self.__class__('cd {directory} && {command}'.format(
            directory=directory,
            command=self.command
        ))

    def wrap(self, command_str):
        command = 'bash -c "{command}"'.format(
            command=self._include_command(
                self.command
            )
        )
        return self.__class__(command_str.format(command=command))


class Executor(HasPerformer):

    def _command_wrapper(self, execute_method):
        @wraps(execute_method)
        def wrapper(command, *args, **kwargs):
            if isinstance(command, str):
                command = Command(command)

            for directory in reversed(self.__directories):
                command = command.change_directory(directory)

            return execute_method(command, *args, **kwargs)
        return wrapper

    def __init__(self, *args, **kwargs):
        self.__directories = []
        self.execute = self._command_wrapper(self.execute)
        super().__init__(*args, **kwargs)

    def execute(self, command, logger=None, writein=None):
        return self.performer.perform(command.command, logger=logger, writein=writein)

    @contextmanager
    def change_directory(self, directory):
        self.__directories.append(directory)
        try:
            yield
        except:
            raise
        finally:
            self.__directories.pop()

    def check_execute(self, command, logger=None, writein=None):
        try:
            self.execute(command, logger=logger, writein=writein)
            return True
        except CommandError:
            return False

    def exists_directory(self, directory):
        return self.check_execute('[ -d {directory} ]'.format(directory=directory))
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
            #     ssh_info = self.performer.execute('echo $SSH_CLIENT')
            #     ip, remote_port, local_port = ssh_info.split()
            #     self.ident = 'control_{ip}_{remote_port}_{local_port}'.format(
            #         ip=ip, remote_port=remote_port, local_port=local_port
            #     )

            self.__isolation_directory = '/tmp/.codev/{ident}'.format(
                ident=self.ident
            )

        return self.__isolation_directory

    def _create_isolation(self):
        self.performer.execute('mkdir -p %s' % self._isolation_directory)

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
        self.performer.execute('rm -rf %s' % self._isolation_directory)

    def _file_exists(self, filepath):
        return self.performer.check_execute('[ -f %s ]' % filepath)

    def _bg_check(self, pid):
        return self.performer.check_execute('ps -p %s -o pid=' % pid)

    def _bg_log(self, logger, skip_lines):
        output = self.performer.execute('tail {output_file} -n+{skip_lines}'.format(
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
        return self.performer.execute(
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
        return self.performer.execute('cat %s' % catfile)

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

        self.performer.execute('echo "" > {output_file} > {error_file} > {exitcode_file} > {pid_file}'.format(
            **isolation._asdict()
        ))

        self.performer.execute(
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
        pid = self.performer.execute(bg_command, writein=writein)

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