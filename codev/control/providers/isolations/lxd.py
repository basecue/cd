
from codev.core.providers.machines.lxd import LXDMachine, LXDMachinesSettings

from codev.control.isolator import Isolator, PrivilegedIsolation


class LXDIsolation(Isolator):
    provider_name = 'lxd'

    def _get(self, ident):
        return PrivilegedIsolation(performer=LXDMachine(performer=self.performer, ident=ident))

    def __init__(self, *args, ident, **kwargs):
        isolation = self._get(ident)
        if isolation.exists() and isolation.is_started():
            return isolation
        else:
            return None

    def get_or_create(self):
        isolation = self._get(ident)

        if isolation.exists():

            if not isolation.is_started():
                isolation.start()

            return isolation, False

        settings = LXDMachinesSettings(data=dict(distribution='ubuntu', release='xenial'))

        # TODO - rethink ssh key management
        ssh_key = self.performer.execute('ssh-add -L')

        isolation.create(settings, ssh_key)

        self.performer.execute(
            'lxc config set {container_name} security.nesting true'.format(
                container_name=isolation.container_name
            )
        )

        # isolation.execute('snap refresh')

        isolation.stop()
        isolation.start()

        # TODO - providers requirements
        isolation.install_packages(
            'lxd',
            'python3-pip', 'libffi-dev', 'libssl-dev',  # for codev
            'python-virtualenv', 'python-dev', 'python3-venv', 'sshpass',  # for ansible task
            'git',  # for git source
            'clsync',  # for share support
        )

        isolation.execute('lxd init --auto')
        return isolation, True

        # uid_start, uid_range, gid_start, gid_range = self._get_id_mapping()
        #
        # isolation.machine.execute("sed -i '/^root:/d' /etc/subuid /etc/subgid")
        # isolation.machine.execute('usermod -v {uid_start}-{uid_end} -w {gid_start}-{gid_end} root'.format(
        #     uid_start=uid_start,
        #     uid_end=uid_start + uid_range - 1,
        #     gid_start=gid_start,
        #     gid_end=gid_start + gid_range - 1
        # ))
        #
        # isolation.machine.execute('echo "lxc.id_map = u 0 {uid_start} {uid_range}" >> /etc/lxc/default.conf'.format(
        #     uid_start=uid_start,
        #     uid_range=uid_range
        # ))
        # isolation.machine.execute('echo "lxc.id_map = g 0 {gid_start} {gid_range}" >> /etc/lxc/default.conf'.format(
        #     gid_start=gid_start,
        #     gid_range=gid_range
        # ))

    # @contextmanager
    # def _environment(self):
    #     env = {}
    #     ssh_auth_sock_local = self.performer.execute('echo $SSH_AUTH_SOCK')
    #     performer_background_runner = None
    #     machine_background_runner = None
    #     ssh_auth_sock_remote = None
    #     if ssh_auth_sock_local and self.performer.check_execute(
    #         '[ -S {ssh_auth_sock_local} ]'.format(
    #             ssh_auth_sock_local=ssh_auth_sock_local
    #         )
    #     ):
    #         performer_background_runner = BackgroundExecutor(performer=self.performer)
    #         machine_background_runner = BackgroundExecutor(performer=self.machine)
    #
    #         ssh_auth_sock_remote = '/tmp/{ident}-ssh-agent-sock'.format(ident=machine_background_runner.ident)
    #
    #         # TODO avoid tcp because security reason
    #         performer_background_runner.execute(
    #             'socat TCP-LISTEN:44444,bind={gateway},fork UNIX-CONNECT:{ssh_auth_sock_local}'.format(
    #                 gateway=self.machine._gateway,
    #                 ssh_auth_sock_local=ssh_auth_sock_local
    #             ),
    #             wait=False
    #         )
    #         machine_background_runner.execute(
    #             'socat UNIX-LISTEN:{ssh_auth_sock_remote},fork TCP:{gateway}:44444'.format(
    #                 gateway=self.machine._gateway,
    #                 ssh_auth_sock_remote=ssh_auth_sock_remote,
    #             ),
    #             wait=False
    #         )
    #         env['SSH_AUTH_SOCK'] = ssh_auth_sock_remote
    #     try:
    #         yield env
    #     finally:
    #         if ssh_auth_sock_remote:
    #             machine_background_runner.kill()
    #             performer_background_runner.kill()
    #
    # def execute(self, command, logger=None, writein=None):
    #     with self._environment() as env:
    #         return self.machine.execute(command, env=env, logger=logger, writein=writein)
    #
    # @contextmanager
    # def change_directory(self, directory):
    #     with self.machine.change_directory(directory):
    #         yield
    #
    # def share(self, source, target, bidirectional=False):
    #     self.machine.share(source, target, bidirectional=bidirectional)
