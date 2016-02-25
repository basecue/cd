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
from codev.configuration import YAMLConfigurationReader
from codev.provider import ConfigurableProvider
from codev.configuration import BaseConfiguration


class RepositoryConfiguration(BaseConfiguration):
    @property
    def url(self):
        return self.data['url']


class RepositoryInstallation(BaseInstallation, ConfigurableProvider):
    configuration_class = RepositoryConfiguration

    def configure(self, performer):
        """
        TODO RENAME method
        :param performer:
        :return:
        """
        performer.execute('apt-get install git -y --force-yes')

        #TODO checking fingerprints instead of copying known_hosts
        # http://serverfault.com/questions/132970/can-i-automatically-add-a-new-host-to-known-hosts
        # http://serverfault.com/questions/447028/non-interactive-git-clone-ssh-fingerprint-prompt
        # http://unix.stackexchange.com/questions/94448/how-to-add-an-ip-range-to-known-hosts
        # https://help.github.com/articles/what-are-github-s-ssh-key-fingerprints/
        # ssh-keyscan -t rsa,dsa github.com 2> /dev/null > /tmp/key && ssh-keygen -lf /tmp/key
        # ssh-keygen -H -F github.com
        # github.com,192.30.252.*,192.30.253.*,192.30.254.*,192.30.255.* ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAq2A7hRGmdnm9tUDbO9IDSwBK6TbQa+PXYPCPy6rbTrTtw7PHkccKrpp0yVhp5HdEIcKr6pLlVDBfOLX9QUsyCOV0wzfjIJNlGEYsdlLJizHhbn2mUjvSAHQqZETYP81eFzLQNnPHt4EVVUh7VfDESU84KezmD5QlWpXLmvU31/yMf+Se8xhHTvKSCZIFImWwoG6mbUoWf9nzpIoaSjB+weqqUUmpaaasXVal72J+UX2B+2RPW3RcT0eOzQgqlJL3RKrTJvdsjE3JEAvGq3lGHSZXy28G3skua2SmVi/w4yCE6gbODqnTWlg7+wC604ydGXA8VJiS5ap43JXiUFFAaQ==

        #TODO lxc has a bug and doesnt know what is the home directory
        performer.execute('mkdir -p /root/.ssh')
        performer.send_file('~/.ssh/known_hosts', '/root/.ssh/known_hosts')

        directory = 'repository'

        if performer.check_execute('[ -d repository ]'):
            performer.check_execute('rm -rf repository')

        if self.options:
            branch_options = '--branch {branch} --single-branch'.format(branch=self.options)
        else:
            branch_options = ''

        performer.execute('git clone {url} {branch_options} {directory}'.format(
            url=self.configuration.url,
            directory=directory,
            branch_options=branch_options
        ))

        #load configuration
        #TODO configuration filepath should be placed anywhere
        # codev_path = os.path.relpath(repo.working_dir)
        # change cli configuration option etc.
        with performer.get_fo('repository/.codev') as codev_file:
            version = YAMLConfigurationReader().from_yaml(codev_file).version

        return directory, version

Installation.register('repository', RepositoryInstallation)
