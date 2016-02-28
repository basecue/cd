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

from contextlib import contextmanager
from paramiko.client import SSHClient, AutoAddPolicy, NoValidConnectionsError
from paramiko.agent import AgentRequestHandler

from logging import getLogger

from codev.performer import Performer, BasePerformer, PerformerError, CommandError
from codev.configuration import BaseConfiguration
from os.path import expanduser
from threading import Thread


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


class SSHperformer(BasePerformer):
    configuration_class = SSHPerformerConfiguration

    def __init__(self, *args, **kwargs):
        super(SSHperformer, self).__init__(*args, **kwargs)
        self.client = None
        self._output_lines = []
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

    def _reader_out(self, stream, logger=None):
        while True:
            line = stream.readline()
            if not line:
                break
            output_line = line.strip()
            self._output_lines.append(output_line)
            (logger or self.output_logger).debug(output_line)

        stream.close()

    def execute(self, command, logger=None, writein=None):
        self.logger.debug('command: %s' % command)
        if not self.client:
            self._connect()
        self._output_lines = []
        stdin, stdout, stderr = self.client.exec_command(command)
        reader_out = Thread(target=self._reader_out, args=(stdout,), kwargs=dict(logger=logger))
        reader_out.start()
        if writein:
            stdin.write(writein)
            stdin.flush()
            stdin.channel.shutdown_write()
        exit_code = stdout.channel.recv_exit_status()
        reader_out.join()

        if exit_code:
            if exit_code:
                err = stderr.read().decode('utf-8').strip()
                self.logger.debug('command error: %s' % err)
                raise CommandError(command, exit_code, err)

        return '\n'.join(self._output_lines)

    def send_file(self, source, target):
        self.logger.debug('Send file: %s %s' % (source, target))
        source = expanduser(source)
        sftp = self.client.open_sftp()
        sftp.put(source, target)
        sftp.close()

    @contextmanager
    def get_fo(self, remote_path):
        from tempfile import SpooledTemporaryFile
        self.logger.debug('SSH Get fo: %s' % (remote_path))
        sftp = self.client.open_sftp()
        with SpooledTemporaryFile(1024000) as fo:
            size = sftp.getfo(remote_path, fo)
            yield fo
        sftp.close()


Performer.register('ssh', SSHperformer)
