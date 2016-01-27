
from paramiko.client import SSHClient, AutoAddPolicy
import subprocess
from urllib.parse import urlparse
from time import sleep

class PerformerError(Exception):
    pass


class LocalPerformer(object):
    def execute(self, command):
        subprocess.call(command, stdin=None, stdout=None, stderr=None, shell=False, timeout=None)


class SSHPerformer(object):
    OUTFILE = 'codev.out'
    ERRFILE = 'codev.err'

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

    def _bg_check(self, pid):
        stdin, stdout, stderr = self.client.exec_command('ps -p %s -o pid=' % pid)
        output = stdout.read().decode('ascii').strip()
        return output == pid

    def _bg_execute(self, command, outfile=OUTFILE, errfile=ERRFILE):
        #run in background
        bg_command = 'nohup %(command)s > %(outfile)s 2> %(errfile)s < /dev/null & echo $!' % {
            'command': command,
            'outfile': outfile,
            'errfile': errfile,
        }
        stdin, stdout, stderr = self.client.exec_command(bg_command)

        #return pid
        pid = stdout.read().decode('ascii').strip()
        if pid.isdigit():
            return pid
        else:
            raise ValueError('not a pid %s' % pid)

    def _cat_file(self, catfile):
        stdin, stdout, stderr = self.client.exec_command('cat %s' % catfile)
        return stdout.read().decode('ascii')

    def _bg_out(self, outfile=OUTFILE):
        return self._cat_file(outfile)

    def _bg_err(self, errfile=ERRFILE):
        return self._cat_file(errfile)

    def _execute(self, command):
        pid = self._bg_execute(command)
        print('PID:', pid)
        while self._bg_check(pid):
            #timeout
            sleep(0.5)
        out = self._bg_out()
        err = self._bg_err()
        return out, err

        # skip_lines = 0
        # out = ''
        # while self._check(pid):
        #     stdin, stdout, stderr = self.client.exec_command('tail -n+%d codev.out' % skip_lines)
        #     out_buffer = stdout.read().decode('ascii')
        #     err_buffer = stderr.read().decode('ascii')
        #     skip_lines += len(skip_lines.splitlines())
        #     out = '%s%s' % (out, out_buffer)
        # return out

    def execute(self, command):
        if not self.client:
            self._connect()
        print('COMMAND:\n', command)
        return self._execute(command)


class Performer(object):
    def __new__(cls, url):
        ident = urlparse(url)
        scheme = ident.scheme
        if scheme == 'ssh':
            return SSHPerformer(ident)



