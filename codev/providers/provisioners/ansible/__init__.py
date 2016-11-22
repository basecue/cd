from .source import AnsibleSource
from .sources import *
from codev.provisioner import Provisioner
from codev.settings import BaseSettings, ProviderSettings
from codev.isolator import Isolator
# from os import environ
import configparser
import os.path
import json

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
    def requirements(self):
        return self.data.get('requirements', None)

    @property
    def directory(self):
        return self.data.get('directory', '')

    @property
    def modules(self):
        return self.data.get('modules', [])

    @property
    def vault_password(self):
        return self.data.get('vault_password', None)

    @property
    def source(self):
        return ProviderSettings(self.data.get('source', {}))


class AnsibleProvisioner(Provisioner):
    provider_name = 'ansible'
    settings_class = AnsibleProvisionerSettings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isolator = Isolator(
            'virtualenv',
            self.performer,
            settings_data=dict(python='2'),
            ident='codev_ansible')

    def install(self):
        # TODO requirements - python-dev, python-virtualenv
        self.isolator.create()
        self.isolator.execute('pip install setuptools')
        self.isolator.execute('pip install --upgrade markupsafe paramiko PyYAML Jinja2 httplib2 six ecdsa==0.11')

        version_add = ''
        if self.settings.version:
            version_add = '==%s' % self.settings.version
        self.isolator.execute('pip install --upgrade ansible{version_add}'.format(version_add=version_add))

        for module in self.settings.modules:
            self.isolator.execute('pip install --upgrade {module}'.format(module=module))

    def run(self, infrastructure, info, vars):
        inventory = configparser.ConfigParser(allow_no_value=True, delimiters=('',))

        # creating inventory
        for machine in infrastructure.machines:
            for group in machine.groups:
                inventory.add_section(group)
                inventory.set(group, machine.ident, '')
            # ansible node additional requirements
            machine.install_packages('python')

        inventory_directory = '/tmp/codev.ansible.inventory'
        if not os.path.exists(inventory_directory):
            os.makedirs(inventory_directory)

        with open(os.path.join(inventory_directory, 'codev_hosts'), 'w+') as inventoryfile:
            inventory.write(inventoryfile)

        ssh_config = '/tmp/codev.ansible.ssh_config'
        with open(ssh_config, 'w+') as ssh_config_file:
            for machine in infrastructure.machines:
                ssh_config_file.write('Host {machine.ident}\n  HostName {machine.ip}\n\n'.format(machine=machine))

        template_vars = {
            'source_directory': self.performer.execute('pwd')
        }
        template_vars.update(info)
        template_vars.update(vars)

        if self.settings.extra_vars:
            extra_vars = ' --extra-vars "{joined_extra_vars}"'.format(
                joined_extra_vars=' '.join(
                    [
                        '{key}={value}'.format(
                            key=key,
                            value=json.dumps(value)
                        ) for key, value in self.settings.extra_vars.items()
                    ]
                )
            )
        else:
            extra_vars = ''

        # custom ssh config with proper hostnames
        env_vars = 'ANSIBLE_SSH_ARGS="-F {ssh_config}" '.format(ssh_config=ssh_config)

        # support for vault password - sending via stdin
        writein = None
        if self.settings.vault_password:
            vault_password_file = ' --vault-password-file=/bin/cat'
            writein = self.settings.vault_password.format(**template_vars)
        else:
            vault_password_file = ''

        # support for different source of ansible configuration
        if self.settings.source.provider:
            source = AnsibleSource(self.settings.source.provider, self.performer, settings_data=self.settings.source.settings_data)
            source.install()
            source_directory = source.directory
        else:
            source_directory = ''

        directory = os.path.join(source_directory, self.settings.directory)
        with self.isolator.change_directory(directory):
            requirements = self.settings.requirements
            if requirements:
                self.isolator.execute('ansible-galaxy install -r {requirements}'.format(requirements=requirements))

            if self.isolator.check_execute('[ -f hosts ]'):
                self.isolator.execute('cp hosts {inventory}'.format(inventory=inventory_directory))

            machine_idents = [machine.ident for machine in infrastructure.machines]

            self.isolator.execute('{env_vars}ansible-playbook -vvv -i {inventory} {playbook} --limit={limit} {extra_vars}{vault_password_file}'.format(
                inventory=inventory_directory,
                playbook=self.settings.playbook,
                limit=','.join(machine_idents),
                extra_vars=extra_vars,
                env_vars=env_vars,
                vault_password_file=vault_password_file

            ), writein=writein)

        return True
