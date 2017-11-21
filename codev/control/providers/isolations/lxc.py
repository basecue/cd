from codev.core.providers.machines.lxc import LXCBaseMachine, LXCMachinesSettings

from codev.control.isolation import PrivilegedIsolation


class LXCIsolation(LXCBaseMachine, PrivilegedIsolation):
    provider_name = 'lxc'

    def __init__(self, *args, **kwargs):
        self.settings = LXCMachinesSettings(data=dict(distribution='ubuntu', release='xenial'))
        super().__init__(*args, **kwargs)

    def exists(self):
        return self.get(ident).exists()

    def create(self):
        super().create()
        isolation.start()

        # TODO - providers requirements
        isolation.install_packages(
            'lxc',
            'python3-pip', 'libffi-dev', 'libssl-dev',  # for codev
            'python-virtualenv', 'python-dev', 'python3-venv', 'sshpass',  # for ansible task
            'git',  # for git source
            'clsync',  # for share support
        )

        isolation.stop()
        isolation.start()
        return isolation

