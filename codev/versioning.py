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

class Version(object):
    def _split_from_string(self, version_string):
        return version_string.split('.')

    def __init__(self, version_string='0'):
        self.version_parts = self._split_from_string(version_string)

    def change(self, change):
        """
        :param change: ie '0.0.1'
        :return: None
        """
        #TODO

    def __cmp__(self, other):
        comparations = map(lambda x, y: cmp(x, y), self.version_parts, other.version_parts)
        for comparation in comparations:
            if comparation != 0:
                return comparation
        return 0

    def __str__(self):
        return '.'.join(map(str, self.version_parts))

