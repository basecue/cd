from .provider import BaseProvider, ConfigurableProvider
from contextlib import contextmanager
from os import path
from time import time
from urllib.parse import urlencode
from codev.scripts import COMMON_SCRIPTS

COMMON_SCRIPTS_PREFIX = 'codev/'
COMMON_SCRIPTS_PATH = '{directory}/scripts'.format(directory=path.dirname(__file__))


class BaseExecutor(object):
    def __init__(self, *args, ident=None, **kwargs):
        self.base_dir = '~'
        self.working_dir = self.base_dir
        self.ident = ident or str(time())
        self.output_logger = getLogger('command_output')
        super(BaseExecutor, self).__init__(*args, **kwargs)

    def check_execute(self, command):
        try:
            self.execute(command)
            return True
        except CommandError:
            return False

    def execute(self, command, logger=None, writein=None):
        raise NotImplementedError()

    def run_script(self, script, arguments=None, logger=None):
        if arguments is None:
            arguments = {}

        # common scripts
        for common_script, script_path in COMMON_SCRIPTS.items():
            script_ident = '{prefix}{common_script}'.format(
                prefix=COMMON_SCRIPTS_PREFIX,
                common_script=common_script
            )
            if script.startswith(script_ident):
                script_replace = '{common_scripts_path}/{script_path}'.format(
                    common_scripts_path=COMMON_SCRIPTS_PATH,
                    script_path=script_path
                )
                script = script.replace(script_ident, script_replace, 1)
                break
        
        return self.execute(script.format(**arguments), writein=urlencode(arguments), logger=logger)

    def run_scripts(self, scripts, common_arguments=None):
        if common_arguments is None:
            common_arguments = {}
        for script, arguments in scripts.items():
            arguments.update(common_arguments)
            self.run_script(script, arguments)

    @contextmanager
    def change_directory(self, directory):
        self.working_dir = path.join(self.base_dir, directory)
        yield
        self.working_dir = self.base_dir


class PerformerError(Exception):
    pass


class CommandError(PerformerError):
    def __init__(self, command, exit_code, error):
        self.command = command
        self.exit_code = exit_code
        self.error = error
        super(CommandError, self).__init__(
            "Command '{command}' failed with exit code '{exit_code}' with error '{error}'".format(
                command=command, exit_code=exit_code, error=error
            )
        )


"""
Output reader
"""
from threading import Thread


class OutputReader(object):
    def __init__(self, output, logger=None, max_lines=None):
        self._output_lines = []
        self._output_reader = Thread(
            target=self._reader,
            args=(output,),
            kwargs=dict(logger=logger, max_lines=max_lines)
        )
        self._output_reader.start()

    def _reader(self, output, logger=None, max_lines=None):
        while max_lines is None or (len(self._output_lines) < max_lines):
            line = output.readline()
            if not line:
                break
            output_line = line.decode('utf-8').rstrip('\n')
            self._output_lines.append(output_line)
            if logger:
                logger.debug(output_line)
        output.close()

    def output(self):
        self._output_reader.join()
        return '\n'.join(self._output_lines)


class BasePerformer(BaseExecutor, ConfigurableProvider):
    def __init__(self, *args, **kwargs):
        super(BasePerformer, self).__init__(*args, **kwargs)
        self.__cache_packages = False

    def install_packages(self, *packages):
        # TODO make this os independent
        not_installed_packages = [package for package in packages if not self._is_package_installed(package)]
        if not_installed_packages:
            self._cache_packages()
            self.execute(
                'DEBIAN_FRONTEND=noninteractive apt-get install {packages} -y --force-yes'.format(
                    packages=' '.join(not_installed_packages)
                )
            )

    def _cache_packages(self):
        if not self.__cache_packages:
            self.execute('apt-get update')
        self.__cache_packages = True

    def _is_package_installed(self, package):
        # http://www.cyberciti.biz/faq/find-out-if-package-is-installed-in-linux/
        # TODO
        # alternative: dpkg-query -W -f='${Status}' {package}
        try:
            return 'install ok installed' == self.execute("dpkg-query -W -f='${{Status}}' {package}".format(package=package))
        except CommandError:
            return False

    def send_file(self, source, target):
        raise NotImplementedError()

    @contextmanager
    def get_fo(self, remote_path):
        yield NotImplementedError()


class Performer(BaseProvider):
    provider_class = BasePerformer

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


class BaseRunner(BaseExecutor):
    def __init__(self, performer, *args, **kwargs):
        self.performer = performer
        super(BaseRunner, self).__init__(*args, **kwargs)


class BackgroundRunner(BaseRunner):

    def __init__(self, *args, **kwargs):
        super(BackgroundRunner, self).__init__(*args, **kwargs)
        self._isolation_cache = None
        self.__isolation_directory = None
        self.logger = getLogger(__name__)

    @property
    def _isolation_directory(self):
        if not self.__isolation_directory:
            if not self.ident:
                ssh_info = self.performer.execute('echo $SSH_CLIENT')
                ip, remote_port, local_port = ssh_info.split()
                self.ident = 'control_{ip}_{remote_port}_{local_port}'.format(
                    ip=ip, remote_port=remote_port, local_port=local_port
                )

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
            'kill {signal}-{pid}'.format(
                pid=pid,
                signal='-%s ' % signal if signal else ''
            )
        )
        # pgid = self.performer.execute('ps -p %s -o pgid=' % pid)
        # return self.performer.execute(
        #     'kill {signal}-{pgid}'.format(
        #         pgid=pgid,
        #         signal='-%s ' % signal if signal else ''
        #     )
        # )

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
                    raise PerformerError('Another process is running.')

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

        bg_command = 'nohup {command_file} > {output_file} 2> {error_file} & echo $! | tee {pid_file}'.format(
            **isolation._asdict()
        )

        # max lines against readline hang
        pid = self.performer.execute(bg_command, writein=writein, max_lines=1)

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
            raise CommandError(command, exit_code, err)

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
            raise PerformerError('No active process.')

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
