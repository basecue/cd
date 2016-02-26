# Copyright (C) 2016  Jan Češpivo <jan.cespivo@gmail.com>
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License along
#     with this program; if not, write to the Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from collections import namedtuple
from contextlib import contextmanager
from paramiko.client import SSHClient, AutoAddPolicy, NoValidConnectionsError
from paramiko.agent import AgentRequestHandler
from time import sleep

from logging import getLogger

from codev.performer import Performer, BasePerformer, PerformerError, CommandError
from codev.configuration import BaseConfiguration
from os.path import expanduser

Isolation = namedtuple('Isolation', ['output_file', 'error_file', 'exitcode_file', 'command_file', 'pid_file', 'temp_file'])


class SSHPerformerConfiguration(BaseConfiguration):
    @property
    def hostname(self):
        return self.data.get('hostname', 'localhost')

    @property
    def port(self):
        return self.data.get('port', None)

    @property
    def username(self):
        return self.data.get('username', None)

    @property
    def password(self):
        return self.data.get('password', None)


OUTPUT_FILE = 'codev.out'
ERROR_FILE = 'codev.err'
EXITCODE_FILE = 'codev.exit'
COMMAND_FILE = 'codev.command'
PID_FILE = 'codev.pid'
TEMP_FILE = 'codev.temp'


class SSHperformer(BasePerformer):
    configuration_class = SSHPerformerConfiguration

    def __init__(self, *args, **kwargs):
        super(SSHperformer, self).__init__(*args, **kwargs)
        self._isolation_cache = None
        self.client = None
        self.logger = getLogger(__name__)

    def _connect(self):
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.client.load_system_host_keys()

        connection_details = {}
        if self.configuration.port:
            connection_details['port'] = self.configuration.port
        if self.configuration.username:
            connection_details['username'] = self.configuration.username
        if self.configuration.password:
            connection_details['password'] = self.configuration.password
        try:
            self.client.connect(self.configuration.hostname, **connection_details)
        except NoValidConnectionsError as e:
            raise PerformerError('Cant connect to %s' % self.configuration.hostname)
        else:
            #ssh agent forwarding
            s = self.client.get_transport().open_session()
            AgentRequestHandler(s)

    @property
    def _isolation_directory(self):
        if not self.isolation_ident:
            ssh_info = self._execute('echo $SSH_CLIENT')
            ip, remote_port, local_port = ssh_info.split()
            self.isolation_ident = 'control_{ip}_{remote_port}_{local_port}'.format(
                ip=ip, remote_port=remote_port, local_port=local_port
            )

        return self.isolation_ident

    def _create_isolation(self):
        self._execute('mkdir -p %s' % self._isolation_directory)

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

    # def _exists_isolation(self):
    #     return self._check_execute('[ -d %s ]' % self.isolation_directory)

    def _file_exists(self, filepath):
        return self._check_execute('[ -f %s ]' % filepath)

    def check_execute(self, command, background=False):
        try:
            self.execute(command, background=background)
            return True
        except CommandError as e:
            return False

    def _check_execute(self, command):
        try:
            self._execute(command)
            return True
        except CommandError as e:
            return False

    def _execute(self, command, ignore_exit_codes=[], writein=None):
        self.logger.debug('command: %s' % command)
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

    def _bg_log(self, logger, skip_lines, omit_last):
        output = self._execute('tail {output_file} -n+{skip_lines}'.format(output_file=self._isolation.output_file, skip_lines=skip_lines))
        if not output:
            return 0
        output_lines = output.splitlines()
        if omit_last:
            output_lines.pop()
        for line in output_lines:
            logger.info(line)
        return len(output_lines)

    def _bg_stop(self, pid):
        return self._execute('kill %s' % pid)

    def _bg_kill(self, pid):
        return self._execute(
            'kill -9 {pid};rm {exitcode_file}'.format(
                pid=pid,
                exitcode_file=self._isolation.exitcode_file
            )
        )

    def _bg_wait(self, pid, logger=None):
        skip_lines = 1
        while self._bg_check(pid):
            if logger:
                skip_lines += self._bg_log(logger, skip_lines, True)
            sleep(0.5)

        if logger:
            self._bg_log(logger, skip_lines, False)

    def _bg_execute(self, command, logger=None):
        isolation = self._isolation

        if self._file_exists(isolation.exitcode_file) and self._cat_file(isolation.exitcode_file) == '':
            if self._file_exists(isolation.pid_file):
                pid = self._cat_file(isolation.pid_file)
                if pid and self._bg_check(pid):
                    raise PerformerError('Another process is running.')

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

        self._bg_wait(pid, logger=logger)

        exit_code = int(self._cat_file(isolation.exitcode_file))

        output = self._cat_file(isolation.output_file)

        if exit_code:
            err = self._cat_file(isolation.error_file)
            raise CommandError(command, exit_code, err)

        return output

    def _cat_file(self, catfile):
        return self._execute('cat %s' % catfile)

    def _get_bg_running_pid(self):
        return self._cat_file(self._isolation.pid_file)

    def send_file(self, source, target):
        self.logger.debug('Send file: %s %s' % (source, target))
        source = expanduser(source)
        sftp = self.client.open_sftp()
        sftp.put(source, target)
        sftp.close()

    # def get_file(self, source, target):
    #     logger.debug('SSH Get file: %s %s' % (source, target))
    #     target = expanduser(target)
    #     sftp = self.client.open_sftp()
    #     sftp.get(source, target)
    #     sftp.close()

    @contextmanager
    def get_fo(self, source):
        from tempfile import SpooledTemporaryFile
        self.logger.debug('SSH Get fo: %s' % (source))
        sftp = self.client.open_sftp()
        with SpooledTemporaryFile(1024000) as fo:
            size = sftp.getfo(source, fo)
            yield fo
        sftp.close()

    @contextmanager
    def get_temp_fo(self):
        @contextmanager
        def opener():
            with self.get_fo(self._isolation.temp_file) as fo:
                yield fo
        yield self._isolation.temp_file, opener

    # @contextmanager
    # def get_temp_file(self, target):
    #     yield self._isolation.temp_file
    #     self.get_file(self._isolation.temp_file, target)
    #
    # @contextmanager
    # def get_temp_fo(self):
    #     yield self._isolation.temp_file
    #     self.get_fo(self._isolation.temp_file)

    @contextmanager
    def send_to_temp_file(self, source):
        self.send_file(source, self._isolation.temp_file)
        yield self._isolation.temp_file
        self.execute('rm -f %(tmpfile)s' % {'tmpfile': self._isolation.temp_file})

    def execute(self, command, logger=None, background=False):
        self.logger.debug('SSH Executing command: %s' % command)
        if not self.client:
            self._connect()
        if background:
            return self._bg_execute(command, logger=logger)
        else:
            return self._execute(command)

    def _control(self, method, *args, **kwargs):
        if not self.client:
            self._connect()

        self.logger.debug('SSH Join command')
        try:
            pid = self._get_bg_running_pid()
        except CommandError as e:
            raise PerformerError('No active isolation.')

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

Performer.register('ssh', SSHperformer)