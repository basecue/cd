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

from codev.configuration import BaseConfiguration
from codev.machines import MachinesProvider, BaseMachinesProvider


class RealMachine(object):
    def __init__(self, host):
        self.host = host


class RealMachinesConfiguration(BaseConfiguration):
    @property
    def hosts(self):
        return self.data.get('hosts')


class RealMachinesProvider(BaseMachinesProvider):
    configuration_class = RealMachinesConfiguration

    def create_machines(self):
        machines = []
        for host in self.configuration.hosts:
            machines.append(RealMachine(host))
        return machines


MachinesProvider.register('real', RealMachinesProvider)