from codev.provision import Provisioner, BaseProvisioner
from codev.configuration import BaseConfiguration
# from os import environ
import configparser

from logging import getLogger
logger = getLogger(__name__)


class AnsibleProvisionConfiguration(BaseConfiguration):
    @property
    def playbook(self):
        return self.data.get('playbook', None)

    @property
    def version(self):
        return self.data.get('version', None)

    @property
    def extra_vars(self):
        return self.data.get('extra_vars', {})

    @property
    def env_vars(self):
        return self.data.get('env_vars', {})


class AnsibleProvision(BaseProvisioner):
    configuration_class = AnsibleProvisionConfiguration

    def install(self):
        self.performer.execute('apt-get install python-dev python-pip -y --force-yes')
        self.performer.execute('pip install setuptools')
        self.performer.execute('pip install --upgrade markupsafe paramiko PyYAML Jinja2 httplib2 six ecdsa==0.11')

        version_add = ''
        if self.configuration.version:
            version_add = '==%s' % self.configuration.version
        self.performer.execute('pip install --upgrade ansible%s' % version_add)

    def run(self, machines_groups):
        playbook = self.configuration.playbook.format(infrastructure=self.infrastructure.name)

        inventory = configparser.ConfigParser(allow_no_value=True, delimiters=('',))
        for name, machines in machines_groups.items():
            inventory.add_section(name)
            for machine in machines:
                # ansible node additional requirements
                machine.install_package('python')
                inventory.set(name, machine.host, '')

        inventory_filepath = 'codev.ansible.inventory'

        with open(inventory_filepath, 'w+') as inventoryfile:
            inventory.write(inventoryfile)

        if self.configuration.extra_vars:
            extra_vars = ' --extra-vars "{joined_extra_vars}"'.format(
                joined_extra_vars=' '.join(
                    [
                        '{key}={value}'.format(key=key, value=value) for key, value in self.configuration.extra_vars.items()
                    ]
                )
            )
        else:
            extra_vars = ''

        # env = {}
        # env.update(environ)
        # env.update(self.configuration.env_vars)

        if self.configuration.env_vars:
            env_vars = '{joined_env_vars} '.format(
                joined_env_vars=' '.join(
                    [
                        '{key}="{value}"'.format(key=key, value=value) for key, value in self.configuration.env_vars.items()
                    ]
                )
            )
        else:
            env_vars = ''

        self.performer.execute('{env_vars}ansible-playbook -i {inventory} {playbook}{extra_vars}'.format(
            inventory=inventory_filepath,
            playbook=playbook,
            extra_vars=extra_vars,
            env_vars=env_vars
        ))
        # self.performer.execute('{env_vars}ansible all -m ping -i {inventory}{extra_vars}'.format(
        #     inventory=inventory_filepath,
        #     playbook=playbook,
        #     extra_vars=extra_vars,
        #     env_vars=env_vars
        # ))
        return True


Provisioner.register('ansible', AnsibleProvision)
