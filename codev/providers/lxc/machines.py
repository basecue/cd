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

import re

from time import sleep
from codev.configuration import BaseConfiguration
from codev.machines import MachinesProvider, BaseMachinesProvider


class LXCMachine(object):
    def __init__(self, perfomer, ident, distribution, release, architecture):
        self.performer = perfomer
        self.ident = ident
        self.distribution = distribution
        self.release = release
        self.architecture = architecture
        self._container_directory = None

    def exists(self):
        output = self.performer.execute('lxc-ls')
        return self.ident in output.split()

    def is_started(self):
        output = self.performer.execute('lxc-info -n {name} -s'.format(
            name=self.ident,
        ))

        r = re.match('^State:\s+(.*)$', output.strip())
        if r:
            state = r.group(1)
        else:
            raise ValueError('o:%s:o' % output)

        if state == 'RUNNING':
            return True
        elif state == 'STOPPED':
            return False
        else:
            raise ValueError('s:%s:s' % state)

    def create(self):
        if not self.exists():
            self.performer.execute('lxc-create -t download -n {name} -- --dist {distribution} --release {release} --arch {architecture}'.format(
                name=self.ident,
                distribution=self.distribution,
                release=self.release,
                architecture=self.architecture
            ))
            self._configure()
            return True
        else:
            return False

    def _configure(self):
        lxc_config = '{container_directory}config'.format(
            container_directory=self.container_directory
        )

        self.performer.execute('echo "lxc.mount.auto = cgroup" >> %s' % lxc_config)
        self.performer.execute('echo "lxc.aa_profile = lxc-container-default-with-nesting" >> %s' % lxc_config)

        self.performer.execute('mkdir -p {isolation_ident}/share && chmod 7777 {isolation_ident}/share'.format(
            isolation_ident=self.ident
        ))
        home_dir = self.performer.execute('pwd')
        #TODO CHECK LAST 0.0 mount option
        self.performer.execute(
            'echo "lxc.mount.entry = {home_dir}/{isolation_ident}/share share none bind 0.0" >> {lxc_config}'.format(
                home_dir=home_dir,
                isolation_ident=self.ident,
                lxc_config=lxc_config
            )
        )
        #TODO REPLACEABLE WITH mount option "create=dir"
        self.performer.execute('lxc-usernsexec -- mkdir -p {container_directory}/rootfs/share'.format(
            container_directory=self.container_directory
        ))

    @property
    def container_directory(self):
        if not self._container_directory:
            lxc_path=self.performer.execute('lxc-config lxc.lxcpath')
            self._container_directory = '{lxc_path}/{container_name}/'.format(
                lxc_path=lxc_path,
                container_name=self.ident
            )
        return self._container_directory

    def start(self):
        if not self.is_started():
            self.performer.execute('lxc-start -n {name}'.format(
                name=self.ident,
            ))

            while not self.ip:
                sleep(0.5)

            return True
        else:
            return False

    @property
    def ip(self):
        output = self.performer.execute('lxc-info -n {name} -i'.format(
            name=self.ident,
        ))

        for line in output.splitlines():
            r = re.match('^IP:\s+([0-9\.]+)$', line)
            if r:
                return r.group(1)

        return None

    @property
    def host(self):
        return self.ip

    def execute(self, command, logger=None, background=False):
        output = self.performer.execute('lxc-attach -n {container_name} -- {command}'.format(
            container_name=self.ident,
            command=command,
        ), logger=logger, background=background)
        return output

    # def execute(self, command, logger=None, background=False):
    #     ssh_auth_sock = self.performer.execute('echo $SSH_AUTH_SOCK')
    #     if ssh_auth_sock and self.performer.check_execute('[ -S %s ]' % ssh_auth_sock):
    #
    #         self.performer.execute('rm -f {isolation_ident}/share/ssh-agent-sock && ln {ssh_auth_sock} {isolation_ident}/share/ssh-agent-sock && chmod 7777 {isolation_ident}/share/ssh-agent-sock'.format(
    #             ssh_auth_sock=ssh_auth_sock,
    #             isolation_ident=self.ident
    #         ))
    #
    #         #possible solution via socat
    #         #https://gist.github.com/mgwilliams/4d929e10024912670152 or https://gist.github.com/schnittchen/a47e40760e804a5cc8b9
    #
    #         env_vars = '-v SSH_AUTH_SOCK=/share/ssh-agent-sock'
    #     else:
    #         env_vars = ''
    #
    #     output = self.performer.execute('lxc-attach {env_vars} -n {container_name} -- {command}'.format(
    #         container_name=self.ident,
    #         command=command,
    #         env_vars=env_vars
    #     ), logger=logger, background=background)
    #     return output


class LXCMachinesConfiguration(BaseConfiguration):
    @property
    def distribution(self):
        return self.data.get('distribution')

    @property
    def release(self):
        return self.data.get('release')

    @property
    def architecture(self):
        return self.data.get('architecture')

    @property
    def number(self):
        return int(self.data.get('number'))


class LXCMachinesProvider(BaseMachinesProvider):
    configuration_class = LXCMachinesConfiguration

    def create_machines(self):
        machines = []
        for i in range(1, self.configuration.number + 1):
            ident = '%s_%000d' % (self.machines_name, i)
            machine = LXCMachine(
                self.performer,
                ident,
                self.configuration.distribution,
                self.configuration.release,
                self.configuration.architecture
            )
            machine.create()
            machine.start()
            machine.execute('bash -c "DEBIAN_FRONTEND=noninteractive apt-get install openssh-server -y --force-yes"')
            machines.append(machine)
        return machines

MachinesProvider.register('lxc', LXCMachinesProvider)
