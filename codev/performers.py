
from paramiko.client import SSHClient, AutoAddPolicy
import subprocess
from urllib.parse import urlparse


class PerformerError(Exception):
    pass


class LocalPerformer(object):
    def execute(self, command):
        subprocess.call(command, stdin=None, stdout=None, stderr=None, shell=False, timeout=None)


class SSHPerformer(object):
    def __init__(self, ident):
        self.ident = ident
        self.client = None

    def _connect(self):
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.client.load_system_host_keys()

        connection_details = {}
        if self.ident.port:
            connection_details['port'] = self.ident.port
        if self.ident.username:
            connection_details['username'] = self.ident.username
        if self.ident.password:
            connection_details['password'] = self.ident.password
        self.client.connect(self.ident.hostname, **connection_details)

    def execute(self, command):
        if not self.client:
            self._connect()
        print('COMMAND:\n', command)
        stdin, stdout, stderr = self.client.exec_command(command)

        output = stdout.read().decode('ascii')
        errors = stderr.read().decode('ascii')
        print('OUTPUT:\n', output)
        print('ERRORS:\n', errors)
        return output, errors


class Performer(object):
    def __new__(cls, url):
        ident = urlparse(url)
        scheme = ident.scheme
        if scheme == 'ssh':
            return SSHPerformer(ident)



