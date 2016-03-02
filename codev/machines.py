from .provider import BaseProvider, ConfigurableProvider
from .performer import BaseRunner, CommandError


class BaseMachine(BaseRunner):
    def __init__(self, *args, **kwargs):
        super(BaseMachine, self).__init__(*args, **kwargs)
        self._cache_packages = False

    def install_package(self, package):
        if not self.is_package_installed(package):
            self.cache_packages()
            self.execute(
                'bash -c "DEBIAN_FRONTEND=noninteractive apt-get install {package} -y --force-yes"'.format(
                    package=package
                )
            )

    def cache_packages(self):
        if not self._cache_packages:
            self.execute('apt-get update')
        self._cache_packages = True

    def is_package_installed(self, package):
        # http://www.cyberciti.biz/faq/find-out-if-package-is-installed-in-linux/
        try:
            return 'Status: install ok installed' in self.execute('dpkg -s {package}'.format(package=package))
        except CommandError:
            return False


class BaseMachinesProvider(ConfigurableProvider):
    def __init__(self, machines_name, performer, *args, **kwargs):
        self.machines_name = machines_name
        self.performer = performer
        super(BaseMachinesProvider, self).__init__(*args, **kwargs)


class MachinesProvider(BaseProvider):
    provider_class = BaseMachinesProvider
