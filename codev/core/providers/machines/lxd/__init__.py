import json
import re
from time import sleep
from contextlib import contextmanager
from logging import getLogger
from os import path

from codev.core.installer import Installer
from codev.core.providers import SSHExecutor
from codev.core.settings import BaseSettings
from codev.core.machines import BaseMachine, Machine

logger = getLogger(__name__)


class LXDBaseMachineSettings(BaseSettings):
    @property
    def distribution(self):
        return self.data.get('distribution')

    @property
    def release(self):
        return self.data.get('release')


class LXDBaseMachine(BaseMachine):
    settings_class = LXDBaseMachineSettings

    @property
    def effective_executor(self):
        return SSHExecutor(settings_data={'hostname': self._ip, 'username': 'root'})

    @property
    def _container_name(self):
        return self.ident.as_file()

    def exists(self):
        output = self.executor.execute(
            'lxc list -cn --format=json ^{container_name}$'.format(
                container_name=self._container_name
            )
        )
        return bool(json.loads(output))

    def is_started(self):
        output = self.executor.execute(
            'lxc info {container_name}'.format(
                container_name=self._container_name
            )
        )
        for line in output.splitlines():
            r = re.match('^Status:\s+(.*)$', line)
            if r:
                state = r.group(1)
                break
        else:
            raise ValueError(output)

        if state == 'Running':
            if self._ip and self.check_execute('runlevel'):
                return True
            else:
                return False
        elif state == 'Stopped':
            return False
        else:
            raise ValueError(f'Bad state: {state}')

    def _wait_for_start(self):
        while not self.is_started():
            sleep(0.5)

    def create(self):
        distribution = self.settings.distribution
        release = self.settings.release

        self.executor.execute(
            f'lxc launch images:{distribution}/{release} {self._container_name}'
        )

        self._wait_for_start()

    def destroy(self):
        self.executor.execute(f'lxc delete {self._container_name} --force')

        # # TODO share
        # self.executor.execute('rm -rf {share_directory}'.format(share_directory=self.share_directory))

    def start(self):
        self.executor.execute(f'lxc start {self._container_name}')

        self._wait_for_start()

        return True

    def stop(self) -> None:
        self.executor.execute(f'lxc stop {self._container_name}')

    @property
    def _ip(self):
        output = self.executor.execute(f'lxc info {self._container_name}')
        for line in output.splitlines():
            r = re.match('^\s+eth0:\s+inet\s+([0-9\.]+)\s+\w+$', line)
            if r:
                return r.group(1)

        return None


class LXDMachine(Machine, LXDBaseMachine):
    provider_name = 'lxd'

    def create(self):
        super(LXDMachine, self).create()
        Installer(executor=self).install_packages('openssh-server')

        # authorize user for ssh
        if self.settings.ssh_key:
            self.execute('mkdir -p .ssh')
            self.execute('tee .ssh/authorized_keys', writein=self.settings.ssh_key)

    # @property
    # def _gateway(self):
    #     if not self.__gateway:
    #         # attempts to get gateway ip
    #         for i in range(3):
    #             self.__gateway = self.executor.execute(
    #                 'lxc exec {container_name} -- ip route | grep default | cut -d " " -f 3'.format(
    #                     container_name=self._container_name
    #                 )
    #             )
    #             if self.__gateway:
    #                 break
    #             else:
    #                 sleep(3)
    #     return self.__gateway
    #
    # @contextmanager
    # def open_file(self, remote_path):
    #     tempfile = '/tmp/codev.{container_name}.tempfile'.format(container_name=self._container_name)
    #     remote_path = self._sanitize_path(remote_path)
    #     self.executor.execute(
    #         'lxc file pull {container_name}/{remote_path} {tempfile}'.format(
    #             container_name=self.container_name,
    #             remote_path=remote_path,
    #             tempfile=tempfile
    #         )
    #     )
    #     try:
    #         with self.executor.open_file(tempfile) as fo:
    #             yield fo
    #     finally:
    #         self.executor.execute('rm {tempfile}'.format(tempfile=tempfile))
    #
    # def send_file(self, source, target):
    #     target = self._sanitize_path(target)
    #
    #     self.executor.execute(
    #         'lxc file push --uid=0 --gid=0 {source} {container_name}/{target}'.format(
    #             source=source,
    #             container_name=self._container_name,
    #             target=target
    #         )
    #     )
    #
    # def execute(self, command, env=None, logger=None, writein=None):
    #     if env is None:
    #         env = {}
    #     env.update({
    #         'HOME': '/root',
    #         'LANG': 'C.UTF-8',
    #         'LC_ALL':  'C.UTF-8'
    #     })
    #
    #     with self.executor.change_directory(self.working_dir):
    #         return self.executor.execute_wrapper(
    #             'lxc exec {env} {container_name} -- {{command}}'.format(
    #                 container_name=self._container_name,
    #                 env=' '.join('--env {var}={value}'.format(var=var, value=value) for var, value in env.items())
    #             ),
    #             command,
    #             logger=logger,
    #             writein=writein
    #         )

    # def share(self, source, target, bidirectional=False):
    #     share_target = '{share_directory}/{target}'.format(
    #         share_directory=self.share_directory,
    #         target=target
    #     )
    #
    #     # copy all files to share directory
    #     # sequence /. just after source paramater makes cp command idempotent
    #     self.executor.execute(
    #         'cp -Ru {source}/. {share_target}'.format(
    #             source=source,
    #             share_target=share_target
    #         )
    #     )
    #
    #     if bidirectional:
    #         self.executor.execute(
    #             'chmod -R go+w {share_target}'.format(
    #                 share_target=share_target
    #             )
    #         )
    #
    #     source_target_background_runner = BackgroundExecutor(
    #         executor=self.executor, ident='share_{container_name}'.format(
    #             container_name=self.container_name
    #         )
    #     )
    #     dir_path = path.dirname(__file__)
    #
    #     # prevent sync loop - if there is no change in file don't sync
    #     # This option may eat a lot of memory on huge file trees. see 'man clsync'
    #     modification_signature = ' --modification-signature "*"' if bidirectional else ''
    #
    #     # TODO keep in mind relative and abs paths
    #     try:
    #         source_target_background_runner.execute(
    #             'TO={share_target}'
    #             ' clsync'
    #             ' --label live'
    #             ' --mode rsyncshell'
    #             ' --delay-sync 2'
    #             ' --delay-collect 3'
    #             ' --watch-dir {source}'
    #             '{modification_signature}'
    #             ' --sync-handler {dir_path}/scripts/clsync-synchandler-rsyncshell.sh'.format(
    #                 modification_signature=modification_signature,
    #                 share_target=share_target,
    #                 source=source,
    #                 dir_path=dir_path
    #             ),
    #             wait=False
    #         )
    #     except CommandError:
    #         pass
    #
    #     if bidirectional:
    #         target_source_background_runner = BackgroundExecutor(
    #             executor=self.executor, ident='share_back_{container_name}'.format(
    #                 container_name=self.container_name
    #             )
    #         )
    #         try:
    #             target_source_background_runner.execute(
    #                 'TO={source}'
    #                 ' clsync'
    #                 ' --label live'
    #                 ' --mode rsyncshell'
    #                 ' --delay-sync 2'
    #                 ' --delay-collect 3'
    #                 ' --watch-dir {share_target}'
    #                 ' --modification-signature "*"'
    #                 ' --sync-handler {dir_path}/scripts/clsync-synchandler-rsyncshell.sh'.format(
    #                     share_target=share_target,
    #                     source=source,
    #                     dir_path=dir_path
    #                 ),
    #                 wait=False
    #             )
    #         except CommandError:
    #             pass
    #
    #     if not self.check_execute('[ -L {target} ]'.format(target=target)):
    #         self.execute(
    #             'ln -s /share/{target} {target}'.format(
    #                 target=target,
    #             )
    #         )
