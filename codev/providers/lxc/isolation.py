from codev.isolation import BaseIsolation, Isolation
from logging import getLogger
from .machines import LXCMachine
from codev.performer import BackgroundRunner, PerformerError
from contextlib import contextmanager


class LXCIsolation(BaseIsolation):
    def __init__(self, *args, **kwargs):

        super(LXCIsolation, self).__init__(*args, **kwargs)
        self.machine = LXCMachine(self.performer, ident=self.ident)
        self.logger = getLogger(__name__)

    def _get_id_mapping(self):
        parent_uid_map, parent_uid_start, parent_uid_range = list(map(int, self.execute('cat /proc/self/uid_map').split()))
        parent_uid_range = min(parent_uid_range, 200000)
        uid_start = int(parent_uid_range / 2)
        uid_range = parent_uid_range - uid_start

        parent_gid_map, parent_gid_start, parent_gid_range = list(map(int, self.execute('cat /proc/self/gid_map').split()))
        parent_gid_range = min(parent_gid_range, 200000)
        gid_start = int(parent_gid_range / 2)
        gid_range = parent_gid_range - gid_start
        return uid_start, uid_range, gid_start, gid_range

    def exists(self):
        return self.machine.exists()

    def destroy(self):
        return self.machine.destroy()

    @property
    def ip(self):
        return self.machine.ip

    @contextmanager
    def get_fo(self, remote_path):
        with self.machine.get_fo(remote_path) as fo:
            yield fo

    def send_file(self, source, target):
        return self.machine.send_file(source, target)

    def create(self):
        try:
            created = self.machine.create('ubuntu', 'wily')
        except:
            created = self.machine.create('ubuntu', 'trusty')

        self.machine.start()
        self.machine.install_package('lxc')
        self.machine.install_package('socat')

        # TODO test uid/gid mapping
        # if created:
        #     uid_start, uid_range, gid_start, gid_range = self._get_id_mapping()
        #
        #     self.execute("sed -i '/^root:/d' /etc/subuid /etc/subgid")
        #     self.execute('usermod -v {uid_start}-{uid_end} -w {gid_start}-{gid_end} root'.format(
        #         uid_start=uid_start,
        #         uid_end=uid_start + uid_range - 1,
        #         gid_start=gid_start,
        #         gid_end=gid_start + gid_range - 1
        #     ))
        #
        #     self.execute('echo "lxc.id_map = u 0 {uid_start} {uid_range}" >> /etc/lxc/default.conf'.format(
        #         uid_start=uid_start,
        #         uid_range=uid_range
        #     ))
        #     self.execute('echo "lxc.id_map = g 0 {gid_start} {gid_range}" >> /etc/lxc/default.conf'.format(
        #         gid_start=gid_start,
        #         gid_range=gid_range
        #     ))

        return created

    @contextmanager
    def _environment(self):
        env = {}
        ssh_auth_sock_local = self.performer.execute('echo $SSH_AUTH_SOCK')
        performer_background_runner = None
        machine_background_runner = None
        ssh_auth_sock_remote = None
        if ssh_auth_sock_local and self.performer.check_execute(
            '[ -S {ssh_auth_sock_local} ]'.format(
                ssh_auth_sock_local=ssh_auth_sock_local
            )
        ):
            performer_background_runner = BackgroundRunner(self.performer)
            machine_background_runner = BackgroundRunner(self.machine)

            ssh_auth_sock_remote = '/tmp/{ident}-ssh-agent-sock'.format(ident=machine_background_runner.ident)

            # TODO avoid tcp because security reason
            performer_background_runner.execute(
                'socat TCP-LISTEN:44444,bind={gateway},fork UNIX-CONNECT:{ssh_auth_sock_local}'.format(
                    gateway=self.machine._gateway,
                    ssh_auth_sock_local=ssh_auth_sock_local
                ),
                wait=False
            )
            machine_background_runner.execute(
                'socat UNIX-LISTEN:{ssh_auth_sock_remote},fork TCP:{gateway}:44444'.format(
                    gateway=self.machine._gateway,
                    ssh_auth_sock_remote=ssh_auth_sock_remote,
                ),
                wait=False
            )
            env['SSH_AUTH_SOCK'] = ssh_auth_sock_remote
        try:
            yield env
        finally:
            if ssh_auth_sock_remote:
                machine_background_runner.kill()
                performer_background_runner.kill()

    def execute(self, command, logger=None, writein=None, max_lines=None):
        with self._environment() as env:
            return self.machine.execute(command, env=env, logger=logger, writein=writein, max_lines=max_lines)

    @contextmanager
    def change_directory(self, directory):
        with self.machine.change_directory(directory):
            yield

    def make_link(self, source, target):
        # experimental
        performer_background_runner = BackgroundRunner(
            self.performer, ident='{share_directory}/{target}'.format(
                share_directory=self.machine.share_directory,
                target=target
            )
        )
        from os import path
        dir_path = path.dirname(__file__)

        try:
            performer_background_runner.execute(
                "TO={share_directory}/{target}"
                " clsync"
                " --label live"
                " --mode rsyncshell"
                " --delay-sync 2"
                " --delay-collect 3"
                " --watch-dir {source}"
                " --sync-handler {dir_path}/scripts/clsync-synchandler-rsyncshell.sh".format(
                    share_directory=self.machine.share_directory,
                    target=target,
                    source=source,
                    dir_path=dir_path
                ),
                wait=False
            )
        except PerformerError:
            pass

        machine_background_runner = BackgroundRunner(
            self.machine, ident=self.ident
        )

        self.machine.send_file(
            '{dir_path}/scripts/clsync-synchandler-rsyncshell.sh'.format(dir_path=dir_path),
            '/usr/bin/clsync-synchandler-rsyncshell.sh'
        )
        self.machine.execute('chmod +x /usr/bin/clsync-synchandler-rsyncshell.sh')

        self.machine.install_package('clsync')
        self.machine.install_package('rsync')

        try:
            machine_background_runner.execute(
                "TO={working_dir}/{target}"
                " clsync"
                " --label live"
                " --mode rsyncshell"
                " --delay-sync 2"
                " --delay-collect 3"
                " --watch-dir /share/{target}"
                " --sync-handler /usr/bin/clsync-synchandler-rsyncshell.sh".format(
                    working_dir=self.machine.working_dir,
                    target=target
                ),
                wait=False
            )
        except PerformerError:
            pass


Isolation.register('lxc', LXCIsolation)
