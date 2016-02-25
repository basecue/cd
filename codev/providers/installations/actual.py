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

from codev.installation import Installation, BaseInstallation
import shutil


class ActualInstallation(BaseInstallation):
    def configure(self, performer):
        #gunzip is default for ubuntu
        # performer.execute('apt-get install gunzip -y --force-yes')
        directory = 'repository'
        archive = shutil.make_archive(directory, 'gztar')
        performer.send_file(archive, archive)
        performer.execute('mkdir -p {directory}'.format(directory=directory))
        performer.execute('tar -xzf {archive} --directory {directory}'.format(archive=archive, directory=directory))

        return directory


Installation.register('actual', ActualInstallation)
