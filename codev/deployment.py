from logging import getLogger
from .provisioner import Provisioner
from .performer import BaseProxyExecutor, CommandError

logger = getLogger(__name__)


class Deployment(BaseProxyExecutor):
    def __init__(self, performer, provisions):
        super().__init__(performer)
        self.performer = performer
        self.provisions = provisions

    def deploy(self, infrastructure, script_info, vars):
        """

        :param infrastructure: infrastructure.Infrastructure
        :param script_info: dict
        :return:
        """

        logger.info('Creating machines...')
        infrastructure.create_machines()

        script_info.update(infrastructure=infrastructure.info)

        for provisioner_name, provisioner_settings in self.provisions.items():
            scripts = provisioner_settings.scripts

            try:
                self.execute_scripts(scripts.onstart, script_info)

                provisioner = Provisioner(provisioner_settings.provider, self.performer, settings_data=provisioner_settings.settings_data)

                name = " '{}'".format(provisioner_name) if provisioner_name else ''
                logger.info("Installing provisioner{name}...".format(name=name))
                provisioner.install()

                logger.info("Running provisioner{name}...".format(name=name))
                provisioner.run(infrastructure, script_info, vars)

            except CommandError as e:
                self.execute_scripts_onerror(scripts.onerror, script_info, e, logger=logger)
                raise
            else:
                try:
                    self.execute_scripts(scripts.onsuccess, script_info)
                except CommandError as e:
                    self.execute_scripts_onerror(scripts.onerror, script_info, e, logger=logger)
                    raise
