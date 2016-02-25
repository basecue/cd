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

from .provider import BaseProvider, ConfigurableProvider


class BaseProvision(ConfigurableProvider):
    def __init__(self, performer, infrastructure_name, *args, **kwargs):
        self.performer = performer
        self.infrastructure_name = infrastructure_name
        super(BaseProvision, self).__init__(*args, **kwargs)

    def install(self):
        raise NotImplementedError()

    def run(self, machines):
        raise NotImplementedError()


class Provision(BaseProvider):
    provider_class = BaseProvision
