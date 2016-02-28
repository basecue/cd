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

from .configuration import BaseConfiguration
from ast import literal_eval


class DebugConfiguration(BaseConfiguration):
    configuration = None
    perform_configuration = None

    @property
    def loglevel(self):
        return self.data.get('loglevel', 'info').lower()

    @property
    def distfile(self):
        return self.data.get('distfile', '')

    @property
    def show_client_exception(self):
        return literal_eval(self.data.get('show_client_exception', 'False'))

    @property
    def repository_url(self):
        return self.data.get('repository_url', None)

    @property
    def configuration_dir(self):
        return self.data.get('configuration_dir', None)

    @property
    def repository_dir(self):
        return self.data.get('repository_dir', None)

    @property
    def disable_version_check(self):
        return literal_eval(self.data.get('disable_version_check', 'False'))


DebugConfiguration.configuration = DebugConfiguration()
DebugConfiguration.perform_configuration = DebugConfiguration()
