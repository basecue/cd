from codev.core.installer import Installer
from codev.core.providers.machines.lxd import LXDBaseMachine, LXDMachinesSettings

from codev.control.isolation import PrivilegedIsolation
from codev.core.settings import BaseSettings


class LXDIsolationSettings(BaseSettings):
    @property
    def distribution(self):
        return self.data.get('distribution', 'ubuntu')

    @property
    def release(self):
        return self.data.get('release', 'xenial')


class LXDIsolation(LXDBaseMachine, PrivilegedIsolation):
    provider_name = 'lxd'
    settings_class = LXDIsolationSettings

    def create(self):
        super().create()
        # TODO - providers requirements
        Installer(executor=self).install_packages(
            'lxc',
            'python3-pip', 'libffi-dev', 'libssl-dev',  # for codev
            'python-virtualenv', 'python-dev', 'python3-venv', 'sshpass',  # for ansible task
            'git',  # for git source
            'clsync',  # for share support
        )

        self.stop()
        self.start()
