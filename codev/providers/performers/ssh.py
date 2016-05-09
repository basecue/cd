from contextlib import contextmanager
from paramiko.client import SSHClient, AutoAddPolicy, NoValidConnectionsError
from paramiko.agent import AgentRequestHandler

from logging import getLogger

from codev.performer import Performer, PerformerError, CommandError, OutputReader
from codev.settings import BaseSettings
from os.path import expanduser


class SSHPerformerSettings(BaseSettings):
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


class SSHperformer(Performer):
    provider_name = 'ssh'
    settings_class = SSHPerformerSettings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = None
        self.logger = getLogger(__name__)

    def _connect(self):
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.client.load_system_host_keys()

        connection_details = {}
        if self.settings.port:
            connection_details['port'] = self.settings.port
        if self.settings.username:
            connection_details['username'] = self.settings.username
        if self.settings.password:
            connection_details['password'] = self.settings.password
        try:
            self.client.connect(self.settings.hostname, **connection_details)
        except NoValidConnectionsError as e:
            raise PerformerError('Cant connect to %s' % self.settings.hostname)
        else:
            #ssh agent forwarding
            s = self.client.get_transport().open_session()
            AgentRequestHandler(s)

    def _paramiko_exec_command(self, command, bufsize=-1, timeout=None):
        # replacement paramiko.client.exec_command(command) for binary output
        # https://github.com/paramiko/paramiko/issues/291
        # inspired by workaround https://gist.github.com/smurn/4d45a51b3a571fa0d35d

        chan = self.client._transport.open_session(timeout=timeout)
        chan.settimeout(timeout)
        chan.exec_command(command)
        stdin = chan.makefile('wb', bufsize)
        stdout = chan.makefile('rb', bufsize)
        stderr = chan.makefile_stderr('rb', bufsize)
        return stdin, stdout, stderr

    def execute(self, command, logger=None, writein=None, max_lines=None):
        self.logger.debug('command: %s' % command)
        if not self.client:
            self._connect()

        stdin, stdout, stderr = self._paramiko_exec_command(command)

        # read stdout asynchronously - in 'realtime'
        output_reader = OutputReader(stdout, logger=logger or self.output_logger, max_lines=max_lines)

        if writein:
            # write writein to stdin
            stdin.write(writein)
            stdin.flush()
            stdin.channel.shutdown_write()

        # wait for end of output
        output = output_reader.output()

        # wait for exit code
        exit_code = stdout.channel.recv_exit_status()

        if exit_code:
            err = stderr.read().decode('utf-8').strip()
            self.logger.debug('command error: %s' % err)
            raise CommandError(command, exit_code, err)

        return output

    def send_file(self, source, target):
        self.logger.debug('Send file: %s %s' % (source, target))
        source = expanduser(source)
        sftp = self.client.open_sftp()
        sftp.put(source, target)
        sftp.close()

    @contextmanager
    def get_fo(self, remote_path):
        from tempfile import SpooledTemporaryFile
        self.logger.debug('SSH Get fo: %s' % remote_path)
        sftp = self.client.open_sftp()
        try:
            with SpooledTemporaryFile(1024000) as fo:
                sftp.getfo(remote_path, fo)
                yield fo
        finally:
            sftp.close()
