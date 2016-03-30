from .provider import BaseProvider, ConfigurableProvider
from .performer import BaseRunner, CommandError


class BaseMachine(BaseRunner):
    def __init__(self, *args, **kwargs):
        super(BaseMachine, self).__init__(*args, **kwargs)
        self.__cache_packages = False

    def install_package(self, package):
        # TODO make this as a module for using in events scripts
        if not self._is_package_installed(package):
            self._cache_packages()
            self.execute(
                'DEBIAN_FRONTEND=noninteractive apt-get install {package} -y --force-yes'.format(
                    package=package
                )
            )

    def _cache_packages(self):
        if not self.__cache_packages:
            self.execute('apt-get update')
        self.__cache_packages = True

    def _is_package_installed(self, package):
        # http://www.cyberciti.biz/faq/find-out-if-package-is-installed-in-linux/
        # TODO
        # alternative: dpkg-query -W -f='${Status}' {package}
        try:
            return 'install ok installed' == self.execute("dpkg-query -W -f='${{Status}}' {package}".format(package=package))
        except CommandError:
            return False


class BaseMachinesProvider(ConfigurableProvider):
    def __init__(self, machines_name, performer, *args, **kwargs):
        self.machines_name = machines_name
        self.performer = performer
        super(BaseMachinesProvider, self).__init__(*args, **kwargs)


class MachinesProvider(BaseProvider):
    provider_class = BaseMachinesProvider
