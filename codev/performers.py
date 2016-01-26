
from paramiko.client import SSHClient, AutoAddPolicy
import subprocess
from urllib.parse import urlparse


class PerformerError(Exception):
    pass


class LocalPerformer(object):
    def execute(self, commands):
        for command in commands:
            subprocess.call(command, stdin=None, stdout=None, stderr=None, shell=False, timeout=None)


class SSHPerformer(object):
    def __init__(self, ident):
        self.ident = ident

    def execute(self, commands):
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        client.load_system_host_keys()

        connection_details = {}
        if self.ident.port:
            connection_details['port'] = self.ident.port
        if self.ident.username:
            connection_details['username'] = self.ident.username
        if self.ident.password:
            connection_details['password'] = self.ident.password
        client.connect(self.ident.hostname, **connection_details)

        for command in commands:
            stdin, stdout, stderr = client.exec_command(command)
            errors = stderr.read().decode('ascii')
            if errors:
                raise PerformerError(errors)


class Performer(object):
    def __new__(cls, url):
        ident = urlparse(url)
        scheme = ident.scheme
        if scheme == 'ssh':
            return SSHPerformer(ident)



