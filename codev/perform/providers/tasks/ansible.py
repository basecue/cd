from typing import Optional, Dict, List, Any

import configparser
import json
import os.path
import logging

from codev.core.providers.machines import VirtualenvBaseMachine
from codev.core.installer import Installer
from codev.core.settings import BaseSettings
from codev.core.utils import Ident
from codev.perform.infrastructure import Infrastructure
from codev.perform.task import Task

logger = logging.getLogger(__name__)


class AnsibleTaskSettings(BaseSettings):
    @property
    def playbook(self) -> Optional[str]:
        return self.data.get('playbook')

    @property
    def version(self) -> Optional[str]:
        return self.data.get('version')

    @property
    def python_version(self) -> str:
        return str(self.data.get('python', '2'))

    @property
    def extra_vars(self) -> Dict[str, str]:
        return self.data.get('extra_vars', {})

    @property
    def env_vars(self) -> Dict[str, str]:
        return self.data.get('env_vars', {})

    @property
    def requirements(self) -> Optional[str]:
        return self.data.get('requirements')

    @property
    def directory(self) -> str:
        return self.data.get('directory', '')

    @property
    def modules(self) -> List[str]:
        return self.data.get('modules', [])

    @property
    def vault_password(self) -> Optional[str]:
        return self.data.get('vault_password')


class AnsibleTask(Task):
    provider_name = 'ansible'
    settings_class = AnsibleTaskSettings

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.virtualenv = VirtualenvBaseMachine(
            executor=self.executor,
            settings_data=dict(python=self.settings.python_version),
            ident=Ident('codevansible')
        )

    def run(self, infrastructure: Infrastructure, input_vars: Dict[str, str], source_directory: str = '') -> bool:
        # TODO requirements - python-dev, python-virtualenv
        # Installer(executor=self.executor).install_packages(
        #     'python-virtualenv', 'python-dev', 'python3-venv', 'sshpass',  # for ansible task
        # )

        self.virtualenv.create()
        # self.virtualenv.execute('pip install --upgrade setuptools==34.0.2')
        # self.virtualenv.execute('pip install --upgrade pycrypto==2.6.1 cffi==1.9.1 markupsafe==0.23 PyYAML==3.12 cffi==1.9.1 cryptography==1.7.1 paramiko==2.1.1 Jinja2==2.9.4 httplib2==0.9.2 six==1.10.0 ecdsa==0.11')

        version_add = ''
        if self.settings.version:
            version_add = '==%s' % self.settings.version
        self.virtualenv.execute(f'pip install --upgrade ansible{version_add}')

        for module in self.settings.modules:
            self.virtualenv.execute(f'pip install --upgrade {module}')

        inventory = configparser.ConfigParser(allow_no_value=True, delimiters=('',))

        # creating inventory
        for machine in infrastructure.machines:
            for group in machine.groups:
                inventory.add_section(group)
                inventory.set(group, machine.ident.as_hostname(), '')
            # ansible node additional requirements
            Installer(executor=machine).install_packages('python')

        inventory_directory = '/tmp/codev.ansible.inventory'
        if not os.path.exists(inventory_directory):
            os.makedirs(inventory_directory)

        with open(os.path.join(inventory_directory, 'codev_hosts'), 'w+') as inventoryfile:
            inventory.write(inventoryfile)

        ssh_config = '/tmp/codev.ansible.ssh_config'
        with open(ssh_config, 'w+') as ssh_config_file:
            for machine in infrastructure.machines:
                ssh_config_file.write(
                    'Host {hostname}\n  HostName {ip}\n\n'.format(
                        hostname=machine.ident.as_hostname(),
                        ip=machine.ip
                    )
                )

        # template_vars = {
        #     'source_directory': self.executor.execute('pwd'),
        #     'ssh_config': ssh_config,
        # }
        # template_vars.update(input_vars)

        # extra vars

        if self.settings.extra_vars:
            extra_vars_file = '/tmp/codev.ansible.extra_vars_file'
            with open(extra_vars_file, 'w+') as extra_vars_fo:
                extra_vars_fo.write(json.dumps(self.settings.extra_vars))

            extra_vars = f' --extra-vars "@{extra_vars_file}"'
        else:
            extra_vars = ''

        # custom ssh config with proper hostnames
        env_vars_dict = dict(
            ANSIBLE_SSH_ARGS=f'-F {ssh_config}'
        )

        env_vars_dict.update(self.settings.env_vars)

        env_vars = '{joined_env_vars} '.format(
            joined_env_vars=' '.join(
                [
                    '{key}="{value}"'.format(
                        key=key,
                        value=value.format(**input_vars) if isinstance(value, str) else value
                    ) for key, value in env_vars_dict.items()
                ]
            )
        )

        # support for vault password - sending via stdin
        writein = None
        if self.settings.vault_password:
            vault_password_file = ' --vault-password-file=/bin/cat'
            writein = self.settings.vault_password.format(**input_vars)
        else:
            vault_password_file = ''

        directory = os.path.join(source_directory, self.settings.directory)
        with self.virtualenv.change_directory(directory):
            requirements = self.settings.requirements
            if requirements:
                self.virtualenv.execute(f'ansible-galaxy install -r {requirements}')

            if self.virtualenv.exists_file('hosts'):
                self.virtualenv.execute(f'cp hosts {inventory_directory}')

            machine_hostnames = [machine.ident.as_hostname() for machine in infrastructure.machines]

            self.virtualenv.execute(
                '{env_vars}ansible-playbook -v -i {inventory} {playbook} --limit={limit} {extra_vars}{vault_password_file}'.format(
                    inventory=inventory_directory,
                    playbook=self.settings.playbook,
                    limit=','.join(machine_hostnames),
                    extra_vars=extra_vars,
                    env_vars=env_vars,
                    vault_password_file=vault_password_file
                ),
                writein=writein
            )

        return True
