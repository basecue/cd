# Copyright (C) 2016  Jan Češpivo <jan.cespivo@gmail.com>
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License along
#     with this program; if not, write to the Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from codev.isolation import BaseIsolationProvider, IsolationProvider
from contextlib import contextmanager
from logging import getLogger
from .machines import LXCMachine
from codev.performer import BackgroundRunner


class LXCIsolation(LXCMachine):
    def __init__(self, *args, **kwargs):
        self.logger = getLogger(__name__)
        super(LXCIsolation, self).__init__('ubuntu', 'wily', *args, **kwargs)

    def _sanitize_path(self, path):
        if path.startswith('~/'):
            path = '{home_dir}/{path}'.format(
                home_dir=self.home_dir,
                path=path[2:]
            )

        if not path.startswith('/'):
            path = '{home_dir}/{path}'.format(
                home_dir=self.home_dir,
                path=path
            )
        return path

    def send_file(self, source, target):
        tempfile = '/tmp/codev.tempfile.send'
        self.performer.send_file(source, tempfile)
        target = self._sanitize_path(target)

        self.performer.execute('lxc-usernsexec -- cp {tempfile} {container_root}{target}'.format(
            tempfile=tempfile,
            target=target,
            container_root=self.container_root
        ))
        self.performer.execute('rm {tempfile}'.format(tempfile=tempfile))

    @contextmanager
    def get_fo(self, remote_path):
        tempfile = '/tmp/codev.tempfile.get'

        remote_path = self._sanitize_path(remote_path)

        self.performer.execute('lxc-usernsexec -- cp {container_root}{remote_path} {tempfile}'.format(
            tempfile=tempfile,
            remote_path=remote_path,
            container_root=self.container_root
        ))
        with self.performer.get_fo(tempfile) as fo:
            yield fo
        self.performer.execute('lxc-usernsexec -- rm {tempfile}'.format(tempfile=tempfile))

    @property
    def home_dir(self):
        return '/root'

    def execute(self, command, logger=None, writein=None, background=False):
        ssh_auth_sock = self.performer.execute('echo $SSH_AUTH_SOCK')
        env_vars = {'HOME': self.home_dir}
        if ssh_auth_sock and self.performer.check_execute('[ -S %s ]' % ssh_auth_sock):
            self.performer.execute('rm -f {share_directory}/ssh-agent-sock && ln {ssh_auth_sock} {share_directory}/ssh-agent-sock && chmod 7777 {share_directory}/ssh-agent-sock'.format(
                share_directory=self.share_directory,
                ssh_auth_sock=ssh_auth_sock,
                isolation_ident=self.isolation_ident
            ))

            #possible solution via socat
            #https://gist.github.com/mgwilliams/4d929e10024912670152 or https://gist.github.com/schnittchen/a47e40760e804a5cc8b9

            env_vars['SSH_AUTH_SOCK'] = '/share/ssh-agent-sock'
        if background:
            performer = BackgroundRunner(self.performer, self.isolation_ident)
        else:
            performer = self.performer
        output = performer.execute('lxc-attach {env} -n {container_name} -- {command}'.format(
            container_name=self.isolation_ident,
            command=command,
            env=' '.join('-v {var}={value}'.format(var=var, value=value) for var, value in env_vars.items())
        ), logger=logger, writein=writein)
        return output


class LXCIsolationProvider(BaseIsolationProvider):
    def __init__(self, *args, **kwargs):
        super(LXCIsolationProvider, self).__init__(*args, **kwargs)
        self._isolation = None

    def create_isolation(self):
        isolation = LXCIsolation(self.performer, self.ident)
        isolation.create()
        isolation.start()

        isolation.execute('apt-get update')
        isolation.execute('bash -c "DEBIAN_FRONTEND=noninteractive apt-get install lxc -y --force-yes"')

        return isolation


IsolationProvider.register('lxc', LXCIsolationProvider)
