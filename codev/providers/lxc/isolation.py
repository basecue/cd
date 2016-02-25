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

from .machines import LXCMachine


class LXCIsolationProvider(BaseIsolationProvider):
    def __init__(self, *args, **kwargs):
        super(LXCIsolationProvider, self).__init__(*args, **kwargs)
        self._machine = None

    def configure_container(self):
        lxc_config = '{container_directory}config'.format(
            container_directory=self.machine.container_directory
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
            container_directory=self.machine.container_directory
        ))

    def _get_architecture(self):
        architecture = self.performer.execute('uname -m')
        if architecture == 'x86_64':
            architecture = 'amd64'
        return architecture

    @property
    def machine(self):
        if not self._machine:
            architecture = self._get_architecture()
            self._machine = LXCMachine(self.performer, self.ident, 'ubuntu', 'wily', architecture)
        return self._machine

    def create_isolation(self):
        created = self.machine.create()

        if created:
            self.configure_container()

        self.machine.start()

        if created:
            self.machine.execute('apt-get update')
            self.machine.execute('bash -c "DEBIAN_FRONTEND=noninteractive apt-get install lxc -y --force-yes"')

        return self.machine


IsolationProvider.register('lxc', LXCIsolationProvider)
