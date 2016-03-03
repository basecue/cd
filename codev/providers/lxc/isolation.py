from codev.isolation import BaseIsolation, Isolation
from contextlib import contextmanager
from logging import getLogger
from .machines import LXCMachine


class LXCIsolation(BaseIsolation):
    def __init__(self, *args, **kwargs):
        super(LXCIsolation, self).__init__(*args, **kwargs)
        self.logger = getLogger(__name__)
        self.machine = None
        self.base_dir = '/root'
        self.machine = LXCMachine(self.performer, ident=self.ident)

    def _sanitize_path(self, path):
        if path.startswith('~/'):
            path = '{base_dir}/{path}'.format(
                base_dir=self.base_dir,
                path=path[2:]
            )

        if not path.startswith('/'):
            path = '{base_dir}/{path}'.format(
                base_dir=self.base_dir,
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
            container_root=self.machine.container_root
        ))
        with self.performer.get_fo(tempfile) as fo:
            yield fo
        self.performer.execute('lxc-usernsexec -- rm {tempfile}'.format(tempfile=tempfile))

    def _execute(self, executor, command, logger=None, writein=None):
        ssh_auth_sock = self.performer.execute('echo $SSH_AUTH_SOCK')
        env_vars = {'HOME': self.machine.base_dir}
        if ssh_auth_sock and self.performer.check_execute('[ -S %s ]' % ssh_auth_sock):
            self.performer.execute('rm -f {share_directory}/ssh-agent-sock && ln {ssh_auth_sock} {share_directory}/ssh-agent-sock && chmod 7777 {share_directory}/ssh-agent-sock'.format(
                share_directory=self.machine.share_directory,
                ssh_auth_sock=ssh_auth_sock,
                ident=self.ident
            ))

            #possible solution via socat
            #https://gist.github.com/mgwilliams/4d929e10024912670152 or https://gist.github.com/schnittchen/a47e40760e804a5cc8b9

            env_vars['SSH_AUTH_SOCK'] = '/share/ssh-agent-sock'
        output = executor.execute('lxc-attach {env} -n {container_name} -- bash -c "cd {base_dir} && {command}"'.format(
            base_dir=self.base_dir,
            container_name=self.ident,
            command=command,
            env=' '.join('-v {var}={value}'.format(var=var, value=value) for var, value in env_vars.items())
        ), logger=logger, writein=writein)
        return output

    def execute(self, command, logger=None, writein=None):
        return self._execute(self.performer, command, logger=logger, writein=writein)

    def background_execute(self, command, logger=None, writein=None):
        return self._execute(self.background_runner, command, logger=logger, writein=writein)

    def send_file(self, source, target):
        tempfile = '/tmp/codev.{ident}.tempfile'.format(ident=self.ident)
        self.performer.send_file(source, tempfile)
        target = self._sanitize_path(target)

        self.performer.execute('lxc-usernsexec -- cp {tempfile} {container_root}{target}'.format(
            tempfile=tempfile,
            target=target,
            container_root=self.machine.container_root
        ))
        self.performer.execute('rm {tempfile}'.format(tempfile=tempfile))

    def create(self):
        created = self.machine.create('ubuntu', 'wily')
        if created:
            #support for net services (ie vpn)
            self.performer.execute('echo "lxc.cgroup.devices.allow = c 10:200 rwm" >> {container_config}'.format(
                container_config=self.machine.container_config
            ))
            self.performer.execute('echo "lxc.mount.entry = /dev/net dev/net none bind,create=dir" >> {container_config}'.format(
                container_config=self.machine.container_config
            ))

        self.machine.start()
        self.machine.install_package('lxc')

        return created

    def destroy(self):
        self.machine = LXCMachine(self.performer, ident=self.ident)
        return self.machine.destroy()

Isolation.register('lxc', LXCIsolation)
