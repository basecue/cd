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
from codev.performer import CommandError
from logging import getLogger
from .machines import LXCMachine


class LXCIsolation(LXCMachine):
    def __init__(self, perfomer, ident):
        self.performer = perfomer
        self.ident = ident
        self.logger = getLogger(__name__)
        architecture = self._get_architecture()

        super(LXCIsolation, self).__init__(perfomer, ident, 'ubuntu', 'wily', architecture)

    def _get_architecture(self):
        architecture = self.performer.execute('uname -m')
        if architecture == 'x86_64':
            architecture = 'amd64'
        return architecture

    def send_file(self, source, target):
        with self.performer.send_to_temp_file(source) as tempfile:
            # self.performer.execute('cat {tempfile} | lxc-attach -n {name} -- tee {target} > /dev/null'.format(
            #     name=self.ident,
            #     tempfile=tempfile,
            #     target=target
            # ))
            self.performer.execute('lxc-usernsexec -- cp {tempfile} {container_dir}rootfs/{target}'.format(
                tempfile=tempfile,
                target=target,
                container_dir=self.container_directory
            ))

    # def get_file(self, source, target):
    #     with self.performer.get_temp_file(target) as tempfile:
    #         #TODO direct access over share directory or with lxc-usernsexec
    #         self.performer.execute('lxc-attach -n {name} -- cat {source} > {tempfile}'.format(
    #             name=self.ident,
    #             tempfile=tempfile,
    #             source=source
    #         ))

    @contextmanager
    def get_fo(self, source):
        with self.performer.get_temp_fo() as (tempfile, opener):
            # self.performer.execute('lxc-attach -n {name} -- cat {source} > {tempfile}'.format(
            #     name=self.ident,
            #     tempfile=tempfile,
            #     source=source
            # ))
            self.performer.execute('cp {container_dir}rootfs/{source} {tempfile}'.format(
                tempfile=tempfile,
                source=source,
                container_dir=self.container_directory
            ))
            with opener() as fo:
                yield fo

    def check_execute(self, command):
        try:
            self.execute(command)
            return True
        except CommandError:
            return False

    def execute(self, command, logger=None, background=False):
        ssh_auth_sock = self.performer.execute('echo $SSH_AUTH_SOCK')
        if ssh_auth_sock and self.performer.check_execute('[ -S %s ]' % ssh_auth_sock):

            self.performer.execute('rm -f {isolation_ident}/share/ssh-agent-sock && ln {ssh_auth_sock} {isolation_ident}/share/ssh-agent-sock && chmod 7777 {isolation_ident}/share/ssh-agent-sock'.format(
                ssh_auth_sock=ssh_auth_sock,
                isolation_ident=self.ident
            ))

            #possible solution via socat
            #https://gist.github.com/mgwilliams/4d929e10024912670152 or https://gist.github.com/schnittchen/a47e40760e804a5cc8b9

            env_vars = '-v SSH_AUTH_SOCK=/share/ssh-agent-sock'
        else:
            env_vars = ''

        output = self.performer.execute('lxc-attach {env_vars} -n {container_name} -- {command}'.format(
            container_name=self.ident,
            command=command,
            env_vars=env_vars
        ), logger=logger, background=background)
        return output


class LXCIsolationProvider(BaseIsolationProvider):
    def __init__(self, *args, **kwargs):
        super(LXCIsolationProvider, self).__init__(*args, **kwargs)
        self._isolation = None

    def create_isolation(self):
        #TODO make it idempotent
        isolation = LXCIsolation(self.performer, self.ident)
        isolation.create()
        isolation.start()

        isolation.execute('apt-get update')
        isolation.execute('bash -c "DEBIAN_FRONTEND=noninteractive apt-get install lxc -y --force-yes"')

        return isolation


IsolationProvider.register('lxc', LXCIsolationProvider)
