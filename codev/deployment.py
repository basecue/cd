from logging import getLogger
from .provisioner import Provisioner
from .performer import BaseProxyExecutor, CommandError

logger = getLogger(__name__)


class Deployment(BaseProxyExecutor):
    def __init__(self, performer, settings):
        super().__init__(performer)
        if settings.provider:
            self.provisioner = Provisioner(settings.provider, performer, settings_data=settings.settings_data)
        else:
            self.provisioner = None
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
        self.execute_scripts(self.scripts.onerror, arguments)

    def deploy(self, infrastructure, script_info, vars):
        """

        :param infrastructure: infrastructure.Infrastructure
        :param script_info: dict
        :return:
        """
        self.execute_scripts(self.scripts.onstart, script_info)
        try:
            logger.info('Creating machines...')
            infrastructure.create_machines()

            script_info.update(infrastructure=infrastructure.info)

            if self.provisioner:
                logger.info('Installing provisioner...')
                self.provisioner.install()

                logger.info('Configuration...')
                self.provisioner.run(infrastructure, script_info, vars)
        except CommandError as e:
            self._onerror(script_info, e)
            return False
        else:
            try:
                self.execute_scripts(self.scripts.onsuccess, script_info)
                return True
            except CommandError as e:
                self._onerror(script_info, e)
                return False
