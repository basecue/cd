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

    def execute(self, command, logger=None, writein=None):
        ssh_auth_sock = self.performer.execute('echo $SSH_AUTH_SOCK')
        env_vars = {
            'HOME': self.base_dir,
            'LANG': 'C.UTF-8',
            'LC_ALL':  'C.UTF-8'
        }
        background_runner = None
        ssh_sock_file = None
        if ssh_auth_sock and self.performer.check_execute('[ -S %s ]' % ssh_auth_sock):
            background_runner = BackgroundRunner(self.performer)
            ssh_sock_file = '/tmp/{ident}-ssh-agent-sock'.format(ident=background_runner.ident)
            background_runner.execute(
                "while true ; do socat UNIX:$SSH_AUTH_SOCK EXEC:'lxc-usernsexec socat STDIN UNIX-LISTEN\:{container_root}{ssh_sock_file}'; done".format(
                    ssh_sock_file=ssh_sock_file,
                    container_root=self.container_root
                ),
                wait=False
            )
            env_vars['SSH_AUTH_SOCK'] = ssh_sock_file

        output = self.performer.execute('lxc-attach {env} -n {container_name} -- bash -c "cd {working_dir} && {command}"'.format(
            working_dir=self.working_dir,
            container_name=self.ident,
            command=command,
            env=' '.join('-v {var}={value}'.format(var=var, value=value) for var, value in env_vars.items())
        ), logger=logger, writein=writein)

        if background_runner:
            background_runner.kill()
            self.performer.execute(
                'lxc-usernsexec rm {container_root}{ssh_sock_file}'.format(
                    ssh_sock_file=ssh_sock_file,
                    container_root=self.container_root
                )
            )

        return output

    # def _execute(self, executor, command, logger=None, writein=None):
    #     ssh_auth_sock = self.performer.execute('echo $SSH_AUTH_SOCK')
    #     env_vars = {
    #         'HOME': self.machine.base_dir,
    #         'LANG': 'C.UTF-8',
    #         'LC_ALL':  'C.UTF-8'
    #     }
    #     if ssh_auth_sock and self.performer.check_execute('[ -S %s ]' % ssh_auth_sock):
    #         # self.performer.execute('rm -f {share_directory}/ssh-agent-sock && ln {ssh_auth_sock} {share_directory}/ssh-agent-sock && chmod 7777 {share_directory}/ssh-agent-sock'.format(
    #         #     share_directory=self.machine.share_directory,
    #         #     ssh_auth_sock=ssh_auth_sock,
    #         #     ident=self.ident
    #         # ))
    #         # env_vars['SSH_AUTH_SOCK'] = '/share/ssh-agent-sock'
    #
    #         self.performer.execute(
    #             "while true ; do socat UNIX:$SSH_AUTH_SOCK EXEC:'lxc-usernsexec socat STDIN UNIX-LISTEN\:{container_root}/tmp/ssh-agent-sock'; done".format(
    #                 container_root=self.machine.container_root
    #             )
    #         )
    #         env_vars['SSH_AUTH_SOCK'] = '/tmp/ssh-agent-sock'
    #         #possible solution via socat
    #         #https://gist.github.com/mgwilliams/4d929e10024912670152 or https://gist.github.com/schnittchen/a47e40760e804a5cc8b9
    #
    #
    #     output = executor.execute('lxc-attach {env} -n {container_name} -- bash -c "cd {base_dir} && {command}"'.format(
    #         base_dir=self.base_dir,
    #         container_name=self.ident,
    #         command=command,
    #         env=' '.join('-v {var}={value}'.format(var=var, value=value) for var, value in env_vars.items())
    #     ), logger=logger, writein=writein)
    #     return output
    #
    # def execute(self, command, logger=None, writein=None):
    #     self.background_runner.execute()
    #     output = self._execute(self.performer, command, logger=logger, writein=writein)
    #     self.background_runner.kill()
    #     return output
    #
    # def background_execute(self, command, logger=None, writein=None):
    #     return self._execute(self.background_runner, command, logger=logger, writein=writein)

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
        if created:
            #support for net services (ie vpn)
            self.performer.execute('echo "lxc.cgroup.devices.allow = c 10:200 rwm" >> {container_config}'.format(
                container_config=self.container_config
            ))
            self.performer.execute('echo "lxc.mount.entry = /dev/net dev/net none bind,create=dir" >> {container_config}'.format(
                container_config=self.container_config
            ))

        self.start()
        self.install_package('lxc')

        return created


Isolation.register('lxc', LXCIsolation)
