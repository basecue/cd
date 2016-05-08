from logging import getLogger
from .provisioner import Provisioner
from .performer import BaseProxyExecutor, CommandError

logger = getLogger(__name__)


class Deployment(BaseProxyExecutor):
    def __init__(self, performer, settings):
        super().__init__(performer)
        self.provisioner = Provisioner(settings.provider, performer, settings_data=settings.specific)
        self.scripts = settings.scripts

    def _onerror(self, arguments, error):
        logger.error(error)
        arguments.update(
            dict(
                command=error.command,
                exit_code=error.exit_code,
                error=error.error
            )
        )
        self.run_scripts(self.scripts.onerror, arguments)

    def deploy(self, infrastructure, script_info):
        """

        :param infrastructure: infrastructure.Infrastructure
        :param script_info: dict
        :return:
        """
        self.run_scripts(self.scripts.onstart, script_info)
        try:
            logger.info('Creating machines...')
            machines_groups = infrastructure.machines_groups(create=True)
            script_info.update(infrastructure=infrastructure.info)

            logger.info('Installing provisioner...')
            self.provisioner.install()

            logger.info('Configuration...')
            self.provisioner.run(machines_groups, script_info)
        except CommandError as e:
            self._onerror(script_info, e)
            return False
        else:
            try:
                self.run_scripts(self.scripts.onsuccess, script_info)
                return True
            except CommandError as e:
                self._onerror(script_info, e)
                return False
