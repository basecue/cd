from codev.isolation import BaseIsolation, Isolation
from contextlib import contextmanager
from logging import getLogger
from .machines import LXCMachine
from codev.performer import BackgroundRunner, PerformerError


class LXCIsolation(LXCMachine, BaseIsolation):
    def __init__(self, *args, **kwargs):
        super(LXCIsolation, self).__init__(*args, **kwargs)
        self.logger = getLogger(__name__)
        self.__gateway = None

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

    @property
    def _gateway(self):
        if not self.__gateway:
            self.__gateway = self.performer.execute(
                'lxc-attach -n {container_name} -- ip route | grep default | cut -d " " -f 3'.format(
                    container_name=self.ident
                )
            )
        return self.__gateway

    @contextmanager
    def get_fo(self, remote_path):
        # TODO try: finally
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
        background_runner_local = None
        background_runner_remote = None
        ssh_auth_sock_remote = None
        if ssh_auth_sock_local and self.performer.check_execute(
            '[ -S {ssh_auth_sock_local} ]'.format(
                ssh_auth_sock_local=ssh_auth_sock_local
            )
        ):
            # TODO tmp to specific, tcp is dangerous, check it
            background_runner_local = BackgroundRunner(self.performer)
            background_runner_remote = BackgroundRunner(self.performer)

            ssh_auth_sock_remote = '/tmp/{ident}-ssh-agent-sock'.format(ident=background_runner_remote.ident)

            background_runner_local.execute(
                'socat TCP-LISTEN:44444,bind={gateway},fork UNIX-CONNECT:{ssh_auth_sock_local}'.format(
                    gateway=self._gateway,
                    ssh_auth_sock_local=ssh_auth_sock_local
                ),
                wait=False
            )
            background_runner_remote.execute(
                'lxc-usernsexec -- socat UNIX-LISTEN:{container_root}{ssh_auth_sock_remote},fork TCP:{gateway}:44444'.format(
                    gateway=self._gateway,
                    ssh_auth_sock_remote=ssh_auth_sock_remote,
                    container_root=self.container_root
                ),
                wait=False
            )
            # background_runner.execute(
            #     "trap '{{ kill 0; exit; kill 0; }}' SIGINT; "
            #     "while true ; "
            #     "do socat UNIX:$SSH_AUTH_SOCK"
            #     " EXEC:'lxc-usernsexec socat STDIN UNIX-LISTEN\:{container_root}{ssh_auth_sock_remote}';"
            #     " test $? -gt 128 && break; done".format(
            #         ssh_auth_sock_remote=ssh_auth_sock_remote,
            #         container_root=self.container_root
            #     ),
            #     wait=False
            # )
            env['SSH_AUTH_SOCK'] = ssh_auth_sock_remote
        try:
            yield env
        finally:
            if ssh_auth_sock_remote:
                background_runner_remote.kill()
                background_runner_local.kill()
                pass

    def execute(self, command, logger=None, writein=None, max_lines=None):
        with self._environment() as env:
            return self.performer.execute('lxc-attach {env} -n {container_name} -- bash -c "cd {working_dir} && {command}"'.format(
                working_dir=self.working_dir,
                container_name=self.ident,
                command=command.replace('$', '\$'),
                env=' '.join('-v {var}={value}'.format(var=var, value=value) for var, value in env.items())
            ), logger=logger, writein=writein, max_lines=max_lines)

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

    def make_link(self, source, target):
        # experimental
        background_runner = BackgroundRunner(
            self.performer, ident='{share_directory}/{target}'.format(
                share_directory=self.share_directory,
                target=target
            )
        )
        from os import path
        dir_path = path.dirname(__file__)

        try:
            background_runner.execute(
                "TO={share_directory}/{target}"
                " clsync"
                " --label live"
                " --mode rsyncshell"
                " --delay-sync 2"
                " --delay-collect 3"
                " --watch-dir {source}"
                " --sync-handler {dir_path}/scripts/clsync-synchandler-rsyncshell.sh".format(
                    share_directory=self.share_directory,
                    target=target,
                    source=source,
                    dir_path=dir_path
                ),
                wait=False
            )
        except PerformerError:
            pass

        background_runner = BackgroundRunner(
            self.machine, ident=self.ident
        )

        self.send_file(
            '{dir_path}/scripts/clsync-synchandler-rsyncshell.sh'.format(dir_path=dir_path),
            '/usr/bin/clsync-synchandler-rsyncshell.sh'
        )
        self.execute('chmod +x /usr/bin/clsync-synchandler-rsyncshell.sh')

        self.install_package('clsync')
        self.install_package('rsync')

        try:
            background_runner.execute(
                "TO={working_dir}/{target}"
                " clsync"
                " --label live"
                " --mode rsyncshell"
                " --delay-sync 2"
                " --delay-collect 3"
                " --watch-dir /share/{target}"
                " --sync-handler /usr/bin/clsync-synchandler-rsyncshell.sh".format(
                    working_dir=self.working_dir,
                    target=target
                ),
                wait=False
            )
        except PerformerError:
            pass


Isolation.register('lxc', LXCIsolation)
