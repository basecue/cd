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

from .machines import MachinesProvider
from .provision import Provision
from .performer import Performer
from logging import getLogger

logger = getLogger(__name__)


class Infrastructure(object):
    def __init__(self, name, configuration):
        self.name = name
        self.configuration = configuration

        self.performer = Performer('local')

        self._provision_provider = Provision(
            configuration.provision.provider,
            self.performer,
            self.name,
            configuration_data=configuration.provision.specific
        )

    def _machines_groups(self):
        machines_groups = {}
        for machines_name, machines_configuration in self.configuration.machines.items():
            machines_provider = MachinesProvider(
                machines_configuration.provider,
                machines_name, self.performer, configuration_data=machines_configuration.specific
            )
            machines_groups[machines_name] = machines_provider.create_machines()
        return machines_groups

    def provision(self):
        logger.info('Installing provisioner...')
        self._provision_provider.install()
        logger.info('Creating machines...')
        machines_groups = self._machines_groups()
        logger.info('Starting provisioning...')
        self._provision_provider.run(machines_groups)
