from codev.provisioner import Provisioner
from codev.settings import BaseSettings
from codev.isolator import Isolator
# from os import environ
import configparser

from logging import getLogger
logger = getLogger(__name__)


class AnsibleProvisionerSettings(BaseSettings):
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


class AnsibleProvisioner(Provisioner):
    provider_name = 'ansible'
    settings_class = AnsibleProvisionerSettings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isolator = Isolator('virtualenv', self.performer, settings_data=dict(python='2', directory=''))

    def install(self):
        # TODO requirements - python-dev, python-virtualenv
        self.isolator.create()
        self.isolator.execute('pip install setuptools')
        self.isolator.execute('pip install --upgrade markupsafe paramiko PyYAML Jinja2 httplib2 six ecdsa==0.11')

        version_add = ''
        if self.settings.version:
            version_add = '==%s' % self.settings.version
        self.isolator.execute('pip install --upgrade ansible%s' % version_add)

    def run(self, machines_groups, info):
        inventory = configparser.ConfigParser(allow_no_value=True, delimiters=('',))
        for machines_group, machines in machines_groups.items():
            inventory.add_section(machines_group)
            for machine in machines:
                # ansible node additional requirements
                machine.install_packages('python')
                inventory.set(machines_group, machine.ip, '')

        inventory_filepath = 'codev.ansible.inventory'

        with open(inventory_filepath, 'w+') as inventoryfile:
            inventory.write(inventoryfile)

        template_vars = {
            'source_directory': self.performer.execute('pwd')
        }
        template_vars.update(info)

        if self.settings.extra_vars:
            extra_vars = ' --extra-vars "{joined_extra_vars}"'.format(
                joined_extra_vars=' '.join(
                    [
                        '{key}={value}'.format(
                            key=key,
                            value=value.format(**template_vars) if isinstance(value, str) else value
                        ) for key, value in self.settings.extra_vars.items()
                    ]
                )
            )
        else:
            extra_vars = ''

        if self.settings.env_vars:
            env_vars = '{joined_env_vars} '.format(
                joined_env_vars=' '.join(
                    [
                        '{key}="{value}"'.format(
                            key=key,
                            value=value.format(**template_vars) if isinstance(value, str) else value
                        ) for key, value in self.settings.env_vars.items()
                    ]
                )
            )
        else:
            env_vars = ''

        self.isolator.execute('{env_vars}ansible-playbook -i {inventory} {playbook}{extra_vars}'.format(
            inventory=inventory_filepath,
            playbook=self.settings.playbook,
            extra_vars=extra_vars,
            env_vars=env_vars
        ))

        return True
