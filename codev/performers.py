
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

    def _execute(self, command, writein=None):
        stdin, stdout, stderr = self.client.exec_command(command)
        if writein:
            stdin.write(writein)
            stdin.flush()
            stdin.channel.shutdown_write()
        err = stderr.read().decode('ascii').strip()

        if err:
            raise PerformerError(err)

        return stdout.read().decode('ascii').strip()

    def _bg_check(self, pid):
        output = self._execute('ps -p %s -o pid=' % pid)
        return output == pid

    def _bg_execute(self, command, mute=False):
        # run in background
        OUTFILE = 'codev.out'
        ERRFILE = 'codev.err'
        EXITCODEFILE = 'codev.exit'
        COMMANDFILE = 'codev.command'

        outfile = '/dev/null' if mute else OUTFILE
        errfile = ERRFILE

        self._execute(
            'tee {commandfile} > /dev/null && chmod +x {commandfile}'.format(
                commandfile=COMMANDFILE
            ),
            writein='%s\n' % command
        )

        bg_command = 'nohup ./{commandfile} > {outfile} 2> {errfile}; echo $? > {exitcodefile} & echo $!'.format(
            commandfile=COMMANDFILE,
            outfile=outfile,
            errfile=ERRFILE,
            exitcodefile=EXITCODEFILE
        )

        pid = self._execute(bg_command)

        self._execute('rm %s' % COMMANDFILE)

        if not pid.isdigit():
            raise ValueError('not a pid %s' % pid)

        while self._bg_check(pid):
            #timeout
            sleep(0.5)

        exit_code = int(self._cat_file(EXITCODEFILE))
        # print(exit_code)

        out = '' if mute else self._cat_file(outfile)

        if exit_code:
            err = self._cat_file(errfile)
            raise PerformerError(err)

        return out

    def _cat_file(self, catfile):
        return self._execute('cat %s' % catfile)

    def send_file(self, source, target):
        sftp = self.client.open_sftp()
        sftp.put(source, target)
        sftp.close()

    def execute(self, command, mute=False, foreground=False):
        if not self.client:
            self._connect()
        # print('COMMAND:\n', command)
        if not foreground:
            return self._bg_execute(command, mute)
        else:
            return self._execute(command)


class Performer(object):
    def __new__(cls, url):
        ident = urlparse(url)
        scheme = ident.scheme
        if scheme == 'ssh':
            return SSHPerformer(ident)


