from codev.isolation import BaseIsolation, Isolation
from contextlib import contextmanager
from logging import getLogger
from .machines import LXCMachine
from codev.performer import BackgroundRunner


class LXCIsolation(LXCMachine, BaseIsolation):
    def __init__(self, *args, **kwargs):
        super(LXCIsolation, self).__init__(*args, **kwargs)
        self.logger = getLogger(__name__)

    def _sanitize_path(self, path):
        if path.startswith('~/'):
            path = '{base_dir}/{path}'.format(
                base_dir=self.base_dir,
                path=path[2:]
            )

        if not path.startswith('/'):
            path = '{working_dir}/{path}'.format(
                working_dir=self.working_dir,
                path=path
            )
        return path

    @contextmanager
    def get_fo(self, remote_path):
        tempfile = '/tmp/codev.{ident}.tempfile'.format(ident=self.ident)

        remote_path = self._sanitize_path(remote_path)

        self.performer.execute('lxc-usernsexec -- cp {container_root}{remote_path} {tempfile}'.format(
            tempfile=tempfile,
            remote_path=remote_path,
            container_root=self.container_root
        ))
        with self.performer.get_fo(tempfile) as fo:
            yield fo
        self.performer.execute('lxc-usernsexec -- rm {tempfile}'.format(tempfile=tempfile))

    @contextmanager
    def _environment(self):
        ssh_auth_sock_local = self.performer.execute('echo $SSH_AUTH_SOCK')
        env = {
            'HOME': self.base_dir,
            'LANG': 'C.UTF-8',
            'LC_ALL':  'C.UTF-8'
        }
        background_runner = None
        ssh_auth_sock_remote = None
        if ssh_auth_sock_local and self.performer.check_execute(
            '[ -S {ssh_auth_sock_local} ]'.format(
                ssh_auth_sock_local=ssh_auth_sock_local
            )
        ):
            background_runner = BackgroundRunner(self.performer)
            # TODO tmp to specific
            ssh_auth_sock_remote = '/tmp/{ident}-ssh-agent-sock'.format(ident=background_runner.ident)
            background_runner.execute(
                "while true ; do socat UNIX:$SSH_AUTH_SOCK EXEC:'lxc-usernsexec socat STDIN UNIX-LISTEN\:{container_root}{ssh_auth_sock_remote}'; done".format(
                    ssh_auth_sock_remote=ssh_auth_sock_remote,
                    container_root=self.container_root
                ),
                wait=False
            )
            env['SSH_AUTH_SOCK'] = ssh_auth_sock_remote

        yield env

        if background_runner:
            background_runner.kill()
            self.performer.check_execute(
                '[ -f {container_root}{ssh_auth_sock_remote} ] && lxc-usernsexec rm {container_root}{ssh_auth_sock_remote}'.format(
                    ssh_auth_sock_local=ssh_auth_sock_local,
                    ssh_auth_sock_remote=ssh_auth_sock_remote,
                    container_root=self.container_root
                )
            )

    def execute(self, command, logger=None, writein=None):
        with self._environment() as env:
            return self.performer.execute('lxc-attach {env} -n {container_name} -- bash -c "cd {working_dir} && {command}"'.format(
                working_dir=self.working_dir,
                container_name=self.ident,
                command=command,
                env=' '.join('-v {var}={value}'.format(var=var, value=value) for var, value in env.items())
            ), logger=logger, writein=writein)

    def send_file(self, source, target):
        tempfile = '/tmp/codev.{ident}.tempfile'.format(ident=self.ident)
        self.performer.send_file(source, tempfile)
        target = self._sanitize_path(target)

        self.performer.execute('lxc-usernsexec -- cp {tempfile} {container_root}{target}'.format(
            tempfile=tempfile,
            target=target,
            container_root=self.container_root
        ))
        self.performer.execute('rm {tempfile}'.format(tempfile=tempfile))

    def create(self):
        created = LXCMachine.create(self, 'ubuntu', 'wily')

        self.start()
        self.install_package('lxc')

        # workaround for bug in lxc
        if created:
            self.execute('systemctl restart lxc-net')
        return created


Isolation.register('lxc', LXCIsolation)
