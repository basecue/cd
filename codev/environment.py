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

from .isolation import IsolationProvider
from .performer import Performer
from .infrastructure import Infrastructure

from logging import getLogger
logger = getLogger(__name__)


class Environment(object):
    def __init__(self, configuration, infrastructure_name, isolation_ident):
        self.performer = Performer(
            configuration.performer.provider,
            configuration_data=configuration.performer.specific
        )

        self._isolation_provider = IsolationProvider(
            configuration.isolation_provider,
            self.performer,
            isolation_ident
        )

        infrastructure_configuration = configuration.infrastructures[infrastructure_name]
        self._infrastructure = Infrastructure(infrastructure_name, infrastructure_configuration)

    def create_isolation(self):
        return self._isolation_provider.create_isolation()

    def provision(self):
        self._infrastructure.provision()




