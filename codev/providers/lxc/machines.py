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
from codev.performer import BaseRunner


class LXCMachine(BaseRunner):
    def __init__(self, distribution, release, *args, **kwargs):
        super(LXCMachine, self).__init__(*args, **kwargs)
        self.distribution = distribution
        self.release = release
        self.__container_directory = None
        self.__share_directory = None

    def exists(self):
        output = self.performer.execute('lxc-ls')
        return self.isolation_ident in output.split()

    def is_started(self):
        output = self.performer.execute('lxc-info -n {name} -s'.format(
            name=self.isolation_ident,
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
            architecture = self._get_architecture()
            self.performer.execute('lxc-create -t download -n {name} -- --dist {distribution} --release {release} --arch {architecture}'.format(
                name=self.isolation_ident,
                distribution=self.distribution,
                release=self.release,
                architecture=architecture
            ))
            self._configure()
            return True
        else:
            return False

    def _get_architecture(self):
        architecture = self.performer.execute('uname -m')
        if architecture == 'x86_64':
            architecture = 'amd64'
        return architecture

    def _configure(self):

        self.performer.execute('echo "lxc.mount.auto = cgroup" >> {container_config}'.format(
            container_config=self.container_config
        ))

        self.performer.execute('echo "lxc.aa_profile = lxc-container-default-with-nesting" >> {container_config}'.format(
            container_config=self.container_config
        ))


        self.performer.execute('mkdir -p {share_directory} && chmod 7777 {share_directory}'.format(
            share_directory=self.share_directory
        ))

        self.performer.execute(
            'echo "lxc.mount.entry = {share_directory} share none bind,create=dir 0.0" >> {container_config}'.format(
                share_directory=self.share_directory,
                isolation_ident=self.isolation_ident,
                container_config=self.container_config
            )
        )
        # #TODO REPLACEABLE WITH mount option "create=dir"
        # self.performer.execute('lxc-usernsexec -- mkdir -p {home_dir}/{container_root}/share'.format(
        #     home_dir=home_dir,
        #     container_root=self.container_root
        # ))

    @property
    def share_directory(self):
        if not self.__share_directory:
            home_dir = self.performer.execute('bash -c "echo ~"')
            return '{home_dir}/{isolation_ident}/share'.format(
                home_dir=home_dir,
                isolation_ident=self.isolation_ident
            )
        return self.__share_directory

    @property
    def _container_directory(self):
        if not self.__container_directory:
            lxc_path = self.performer.execute('lxc-config lxc.lxcpath')
            self.__container_directory = '{lxc_path}/{container_name}'.format(
                lxc_path=lxc_path,
                container_name=self.isolation_ident
            )
        return self.__container_directory

    @property
    def container_root(self):
        return '{container_directory}/rootfs'.format(container_directory=self._container_directory)

    @property
    def container_config(self):
        return '{container_directory}/config'.format(container_directory=self._container_directory)

    def start(self):
        if not self.is_started():
            self.performer.execute('lxc-start -n {name}'.format(
                name=self.isolation_ident,
            ))

            while not self.ip:
                sleep(0.5)

            return True
        else:
            return False

    @property
    def ip(self):
        output = self.performer.execute('lxc-info -n {name} -i'.format(
            name=self.isolation_ident,
        ))

        for line in output.splitlines():
            r = re.match('^IP:\s+([0-9\.]+)$', line)
            if r:
                return r.group(1)

        return None

    @property
    def host(self):
        return self.ip

    def execute(self, command, logger=None, writein=None):
        output = self.performer.execute('lxc-attach -n {container_name} -- {command}'.format(
            container_name=self.isolation_ident,
            command=command,
        ), logger=logger, writein=writein)
        return output


class LXCMachinesConfiguration(BaseConfiguration):
    @property
    def distribution(self):
        return self.data.get('distribution')

    @property
    def release(self):
        return self.data.get('release')

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
                self.configuration.distribution,
                self.configuration.release,
                self.performer,
                ident
            )
            machine.create()
            machine.start()
            machine.execute('bash -c "DEBIAN_FRONTEND=noninteractive apt-get install openssh-server -y --force-yes"')
            machines.append(machine)
        return machines

MachinesProvider.register('lxc', LXCMachinesProvider)
