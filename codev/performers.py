
from paramiko.client import SSHClient, AutoAddPolicy
import subprocess
from urllib.parse import urlparse
from time import sleep

from logging import getLogger
logger = getLogger(__name__)


class PerformerError(Exception):
    def __init__(self, command, exit_code, error):
        super(PerformerError, self).__init__(
            "Command '{command}' failed with exit code '{exit_code}' with error '{error}'".format(
                command=command, exit_code=exit_code, error=error
            )
        )


OUTPUT_FILE = 'codev.out'
ERROR_FILE = 'codev.err'
EXITCODE_FILE = 'codev.exit'
COMMAND_FILE = 'codev.command'


class LocalPerformer(object):
    def execute(self, command):
        return subprocess.check_output(command, stdin=None, stderr=None, shell=False, timeout=None)

    def send_file(self, source, target):
        subprocess.check_output('cp', source, target, stdin=None, stderr=None, shell=False, timeout=None)


class SSHperformer(object):
    def __init__(self, parsed_url, isolation_directory):
        self.isolation_directory = isolation_directory
        self.parsed_url = parsed_url
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
        self.client.connect(self.parsed_url.hostname, **connection_details)
        self._create_isolation()

    def _create_isolation(self):
        self._execute('mkdir -p %s' % self.isolation_directory)

        self.output_file, self.error_file, self.exitcode_file, self.command_file = map(
            lambda f: '%s/%s' % (self.isolation_directory, f),
            [OUTPUT_FILE, ERROR_FILE, EXITCODE_FILE, COMMAND_FILE]
        )

    def _execute(self, command, ignore_exit_codes=[], writein=None):
        logger.debug('Executing command: %s' % command)
        stdin, stdout, stderr = self.client.exec_command(command)
        if writein:
            stdin.write(writein)
            stdin.flush()
            stdin.channel.shutdown_write()

        exit_code = stdout.channel.recv_exit_status()
        if exit_code and exit_code not in ignore_exit_codes:
            if exit_code:
                err = stderr.read().decode('ascii').strip()
                raise PerformerError(command, exit_code, err)

        return stdout.read().decode('ascii').strip()

    def _bg_check(self, pid):
        output = self._execute('ps -p %s -o pid=' % pid, ignore_exit_codes=[1])
        return output == pid

    def _bg_log(self, skip_lines, omit_last):
        output = self._execute('tail {output_file} -n+{skip_lines}'.format(output_file=self.output_file, skip_lines=skip_lines))
        output_lines = output.splitlines()
        if omit_last:
            output_lines.pop()
        for line in output_lines:
            logger.debug(line)
        return len(output_lines)

    def _bg_execute(self, command, ignore_exit_codes):
        # run in background
        errfile = self.error_file
        self._execute('echo "" > {output_file} > {error_file} > {exitcode_file}'.format(
            output_file=self.output_file,
            error_file=self.error_file,
            exitcode_file=self.exitcode_file
        ))

        self._execute(
            'tee {command_file} > /dev/null && chmod +x {command_file}'.format(
                command_file=self.command_file
            ),
            writein='%s\n' % command
        )

        bg_command = 'nohup ./{command_file} > {output_file} 2> {error_file}; echo $? > {exitcode_file} & echo $!'.format(
            command_file=self.command_file,
            output_file=self.output_file,
            error_file=self.error_file,
            exitcode_file=self.exitcode_file
        )

        pid = self._execute(bg_command)

        if not pid.isdigit():
            raise ValueError('not a pid %s' % pid)

        skip_lines = 0
        while self._bg_check(pid):
            skip_lines += self._bg_log(skip_lines, True)
            #TODO timeout
            sleep(0.5)

        self._bg_log(skip_lines, False)

        exit_code = int(self._cat_file(self.exitcode_file))

        out = self._cat_file(self.output_file)

        if exit_code and exit_code not in ignore_exit_codes:
            err = self._cat_file(errfile)
            raise PerformerError(command, exit_code, err)

        return out

    def _cat_file(self, catfile):
        return self._execute('cat %s' % catfile)

    def send_file(self, source, target):
        sftp = self.client.open_sftp()
        sftp.put(source, target)
        sftp.close()

    def execute(self, command, ignore_exit_codes=[]):
        if not self.client:
            self._connect()
        return self._bg_execute(command, ignore_exit_codes)


class Performer(object):
    def __new__(cls, url, isolation_ident):
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme
        if scheme == 'ssh':
            return SSHperformer(parsed_url, isolation_ident)
