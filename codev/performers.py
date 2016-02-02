
from paramiko.client import SSHClient, AutoAddPolicy
import subprocess
from urllib.parse import urlparse
from time import sleep


class PerformerError(Exception):
    pass


class LocalPerformer(object):
    def execute(self, command):
        return subprocess.check_output(command, stdin=None, stderr=None, shell=False, timeout=None)

    def send_file(self, source, target):
        subprocess.check_output('cp', source, target, stdin=None, stderr=None, shell=False, timeout=None)


class SSHPerformer(object):
    def __init__(self, ident):
        self.ident = ident
        self.client = None

    def _connect(self):
        print('CONNECT')
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

    def _bg_execute(self, command, outfile, errfile):
        # run in background
        bg_command = 'nohup %(command)s > %(outfile)s 2> %(errfile)s & echo $!' % {
            'command': command,
            'outfile': outfile,
            'errfile': errfile,
        }
        stdin, stdout, stderr = self.client.exec_command(bg_command)
        err = stderr.read().decode('ascii').strip()

        if err:
            raise PerformerError(err)

        # return pid
        pid = stdout.read().decode('ascii').strip()
        if pid.isdigit():
            return pid
        else:
            raise ValueError('not a pid %s' % pid)

    def _cat_file(self, catfile):
        stdin, stdout, stderr = self.client.exec_command('cat %s' % catfile)
        return stdout.read().decode('ascii')

    def _execute(self, command, mute=False):
        """
        TODO refaktorize I dont like this code
        :param command:
        :param mute:
        :return:
        """
        OUTFILE = 'codev.out'
        ERRFILE = 'codev.err'

        outfile = '/dev/null' if mute else OUTFILE
        errfile = ERRFILE

        pid = self._bg_execute(command, outfile, errfile)
        print('PID:', pid)
        while self._bg_check(pid):
            #timeout
            sleep(0.5)

        out = '' if mute else self._cat_file(outfile)
        err = self._cat_file(errfile)
        if err:
            raise PerformerError(err)

        return out

        # skip_lines = 0
        # out = ''
        # while self._check(pid):
        #     stdin, stdout, stderr = self.client.exec_command('tail -n+%d codev.out' % skip_lines)
        #     out_buffer = stdout.read().decode('ascii')
        #     err_buffer = stderr.read().decode('ascii')
        #     skip_lines += len(skip_lines.splitlines())
        #     out = '%s%s' % (out, out_buffer)
        # return out

    def send_file(self, source, target):
        sftp = self.client.open_sftp()
        sftp.put(source, target)
        sftp.close()

    def execute(self, command, mute=False):
        if not self.client:
            self._connect()
        print('COMMAND:\n', command)
        return self._execute(command, mute)


class Performer(object):
    def __init__(self, url):
        ident = urlparse(url)
        scheme = ident.scheme
        if scheme == 'ssh':
            self._performer = SSHPerformer(ident)

    def execute(self, command, mute=False):
        return self._performer.execute(command, mute=mute)

    def send_file(self, source, target):
        return self._performer.send_file(source, target)


