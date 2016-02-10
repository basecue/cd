
from paramiko.client import SSHClient, AutoAddPolicy, NoValidConnectionsError
from subprocess import Popen, PIPE, call
from urllib.parse import urlparse
from time import sleep
from threading import Thread

from logging import getLogger
from .logging import command_logger

logger = getLogger(__name__)


class PerformerError(Exception):
    pass


class CommandError(PerformerError):
    def __init__(self, command, exit_code, error):
        super(CommandError, self).__init__(
            "Command '{command}' failed with exit code '{exit_code}' with error '{error}'".format(
                command=command, exit_code=exit_code, error=error
            )
        )


OUTPUT_FILE = 'codev.out'
ERROR_FILE = 'codev.err'
EXITCODE_FILE = 'codev.exit'
COMMAND_FILE = 'codev.command'
PID_FILE = 'codev.pid'


class LocalPerformer(object):
    def __init__(self):
        self._output_lines = []
        self._error_lines = []

    def _reader_out(self, stream):
        while True:
            line = stream.readline()
            if not line:
                break
            output_line = line.decode('utf-8').strip()
            self._output_lines.append(output_line)
            command_logger.info(output_line)
        stream.close()

    def _reader_err(self, stream):
        while True:
            line = stream.readline()
            if not line:
                break
            output_line = line.decode('utf-8').strip()
            self._error_lines.append(output_line)
        stream.close()

    # def _terminator(self, process):
    #     while process.poll() is None:
    #         #check file
    #         process.terminate()

    def execute(self, command):
        logger.debug('Executing LOCAL command: %s' % command)
        self._output_lines = []
        self._error_lines = []
        process = Popen(command.split(), stdout=PIPE, stderr=PIPE)
        reader_out = Thread(target=self._reader_out, args=(process.stdout,))
        reader_out.start()
        reader_err = Thread(target=self._reader_err, args=(process.stderr,))
        reader_err.start()
        # terminator = Thread(target=self._terminator, args=(process,))
        # terminator.start()
        exit_code = process.wait()
        if exit_code:
            raise CommandError(command, exit_code, '\n'.join(self._error_lines))
        return '\n'.join(self._output_lines)

    def send_file(self, source, target):
        call('cp', source, target)


from collections import namedtuple
Isolation = namedtuple('Isolation', ['output_file', 'error_file', 'exitcode_file', 'command_file', 'pid_file'])


class SSHperformer(object):
    def __init__(self, parsed_url, isolation_ident=None):
        self.isolation_ident = isolation_ident
        self.parsed_url = parsed_url
        self._bg_isolation_cache = None
        self.client = None

    def _connect(self):
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.client.load_system_host_keys()

        connection_details = {}
        if self.parsed_url.port:
            connection_details['port'] = self.parsed_url.port
        if self.parsed_url.username:
            connection_details['username'] = self.parsed_url.username
        if self.parsed_url.password:
            connection_details['password'] = self.parsed_url.password
        try:
            self.client.connect(self.parsed_url.hostname, **connection_details)
        except NoValidConnectionsError as e:
            raise PerformerError('Cant connect to %s' % self.parsed_url.hostnam)

    @property
    def _bg_isolation_directory(self):
        if not self.isolation_ident:
            ssh_info = self._execute('echo $SSH_CLIENT')
            ip, remote_port, local_port = ssh_info.split()
            self.isolation_ident = 'control_{ip}_{remote_port}_{local_port}'.format(
                ip=ip, remote_port=remote_port, local_port=local_port
            )

        return self.isolation_ident

    def _create_bg_isolation(self):
        self._execute('mkdir -p %s' % self._bg_isolation_directory)

        output_file, error_file, exitcode_file, command_file, pid_file = map(
            lambda f: '%s/%s' % (self._bg_isolation_directory, f),
            [OUTPUT_FILE, ERROR_FILE, EXITCODE_FILE, COMMAND_FILE, PID_FILE]
        )

        return Isolation(
            command_file=command_file,
            output_file=output_file,
            error_file=error_file,
            exitcode_file=exitcode_file,
            pid_file=pid_file
        )

    @property
    def _bg_isolation(self):
        if not self._bg_isolation_cache:
            self._bg_isolation_cache = self._create_bg_isolation()
        return self._bg_isolation_cache

    # def _exists_isolation(self):
    #     return self._check_execute('[ -d %s ]' % self.isolation_directory)

    def _check_execute(self, command):
        try:
            self._execute(command)
            return True
        except CommandError as e:
            return False

    def _execute(self, command, ignore_exit_codes=[], writein=None):
        logger.debug('command: %s' % command)
        stdin, stdout, stderr = self.client.exec_command(command)
        if writein:
            stdin.write(writein)
            stdin.flush()
            stdin.channel.shutdown_write()

        exit_code = stdout.channel.recv_exit_status()
        if exit_code and exit_code not in ignore_exit_codes:
            if exit_code:
                err = stderr.read().decode('utf-8').strip()
                raise CommandError(command, exit_code, err)

        return stdout.read().decode('utf-8').strip()

    def _bg_check(self, pid):
        return self._execute('ps -p %s -o pid=' % pid, ignore_exit_codes=[1]) == pid

    def _bg_log(self, skip_lines, omit_last):
        output = self._execute('tail {output_file} -n+{skip_lines}'.format(output_file=self._bg_isolation.output_file, skip_lines=skip_lines))
        if not output:
            return 0
        output_lines = output.splitlines()
        if omit_last:
            output_lines.pop()
        for line in output_lines:
            command_logger.info(line)
        return len(output_lines)

    def _bg_wait(self, pid):
        skip_lines = 0
        while self._bg_check(pid):
            skip_lines += self._bg_log(skip_lines, True)
            sleep(0.5)

        self._bg_log(skip_lines, False)

    def _bg_execute(self, command):
        # run in background
        isolation = self._bg_isolation

        self._execute('echo "" > {output_file} > {error_file} > {exitcode_file} > {pid_file}'.format(
            **isolation._asdict()
        ))

        self._execute(
            'tee {command_file} > /dev/null && chmod +x {command_file}'.format(
                **isolation._asdict()
            ),
            writein='{command}; echo $? > {exitcode_file}\n'.format(
                command=command,
                exitcode_file=isolation.exitcode_file
            )
        )

        bg_command = 'nohup ./{command_file} > {output_file} 2> {error_file} & echo $! | tee {pid_file}'.format(
            **isolation._asdict()
        )

        pid = self._execute(bg_command)

        if not pid.isdigit():
            raise ValueError('not a pid %s' % pid)

        self._bg_wait(pid)

        exit_code = int(self._cat_file(isolation.exitcode_file))

        output = self._cat_file(isolation.output_file)

        if exit_code:
            err = self._cat_file(isolation.error_file)
            raise CommandError(command, exit_code, err)

        return output

    def _cat_file(self, catfile):
        return self._execute('cat %s' % catfile)

    def _get_bg_running_pid(self):
        return self._cat_file(self._bg_isolation.pid_file)

    def send_file(self, source, target):
        sftp = self.client.open_sftp()
        sftp.put(source, target)
        sftp.close()

    def execute(self, command):
        logger.debug('Executing SSH command: %s' % command)
        if not self.client:
            self._connect()
        return self._bg_execute(command)

    def join(self):
        if not self.client:
            self._connect()

        logger.debug('Join SSH command')
        try:
            pid = self._get_bg_running_pid()
        except CommandError as e:
            raise PerformerError('No active isolation %s' % self._bg_isolation_directory)
        if pid:
            self._bg_wait(pid)
        else:
            raise PerformerError('No running command.')


class Performer(object):
    def __new__(cls, url, isolation_ident=None):
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme
        if scheme == 'ssh':
            return SSHperformer(parsed_url, isolation_ident=isolation_ident)
