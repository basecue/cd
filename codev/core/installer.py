from typing import Optional

from .executor import HasExecutor, CommandError

DISTRIBUTION_ISSUES = {
    'debian': 'Debian',
    'ubuntu-core': 'Ubuntu Core',
    'ubuntu': 'Ubuntu',
    'arch': 'Arch Linux',
}


class InstallerError(Exception):
    pass


class Installer(HasExecutor):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__cache_packages = False
        self.__distribution: Optional[str] = None

    def install_packages(self, *packages: str) -> None:
        # TODO make this os independent
        not_installed_packages = [package for package in packages if not self._is_package_installed(package)]
        if not_installed_packages:
            self._cache_packages()
            if self._distribution() in ('debian', 'ubuntu'):
                self.executor.execute(
                    'DEBIAN_FRONTEND=noninteractive apt-get install {packages} -y --force-yes'.format(
                        packages=' '.join(not_installed_packages)
                    )
                )
            elif self._distribution() == 'ubuntu-core':
                self.executor.execute(
                    'snap install {packages}'.format(
                        packages=' '.join(not_installed_packages)
                    )
                )
            elif self._distribution() == 'arch':
                self.executor.execute(
                    'pacman -S {packages} --noconfirm'.format(
                        packages=' '.join(not_installed_packages)
                    )
                )

    def _distribution(self) -> str:
        if not self.__distribution:
            issue = self.executor.execute('cat /etc/issue')
            for distribution, issue_start in DISTRIBUTION_ISSUES.items():
                if issue.startswith(issue_start):
                    self.__distribution = distribution
                    break
            else:
                raise InstallerError('Unknown distribution')
        return self.__distribution

    def _cache_packages(self) -> None:
        if not self.__cache_packages:
            if self._distribution() in ('debian', 'ubuntu'):
                self.executor.execute('apt-get update')
        self.__cache_packages = True

    def _is_package_installed(self, package: str) -> bool:
        # http://www.cyberciti.biz/faq/find-out-if-package-is-installed-in-linux/
        # TODO make this os independent
        try:
            if self._distribution() in ('debian', 'ubuntu'):
                return 'install ok installed' == self.executor.execute(
                    "dpkg-query -W -f='${{Status}}' {package}".format(package=package))
            elif self._distribution() == 'arch':
                return self.executor.check_execute("pacman -Qi {package}".format(package=package))
        except CommandError:
            return False
