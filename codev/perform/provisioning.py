from logging import getLogger

from codev.core.performer import ScriptExecutor, CommandError

from .provisioner import Provisioner


logger = getLogger(__name__)


class Provisioning(ScriptExecutor):
    def __init__(self, provisions, infrastructure, *args, **kwargs):
        self.provisions = provisions
        self.infrastructure = infrastructure
        super().__init__(*args, **kwargs)

    def run(self, status, input_vars):
        # TODO
        # scripts = self.settings.scripts

        try:
            # TODO
            # self.execute_scripts(scripts.onstart, status)

            self._run(self.infrastructure, status, input_vars)

        except CommandError as e:
            # TODO
            # self.execute_scripts_onerror(scripts.onerror, status, e, logger=logger)
            return False
        else:
            try:
                # TODO
                # self.execute_scripts(scripts.onsuccess, status)
                return True
            except CommandError as e:
                # TODO
                # self.execute_scripts_onerror(scripts.onerror, status, e, logger=logger)
                return False

    def _run(self, infrastructure, script_info, input_vars):
        """

        :param infrastructure: infrastructure.Infrastructure
        :param script_info: dict
        :return:
        """

        logger.info('Creating machines...')
        infrastructure.create_machines()

        script_info.update(infrastructure=infrastructure.status)

        for provisioner_name, provisioner_settings in self.provisions.items():
            # TODO
            # scripts = provisioner_settings.scripts

            try:
                # TODO
                # self.execute_scripts(scripts.onstart, script_info)

                provisioner = Provisioner(provisioner_settings.provider, performer=self.performer, settings_data=provisioner_settings.settings_data)

                name = " '{}'".format(provisioner_name) if provisioner_name else ''
                logger.info("Installing provisioner{name}...".format(name=name))
                provisioner.install()

                logger.info("Running provisioner{name}...".format(name=name))
                provisioner.run(infrastructure, script_info, input_vars)

            except CommandError as e:
                # TODO
                # self.execute_scripts_onerror(scripts.onerror, script_info, e, logger=logger)
                raise
            else:
                try:
                    # TODO
                    # self.execute_scripts(scripts.onsuccess, script_info)
                    pass
                except CommandError as e:
                    # TODO
                    # self.execute_scripts_onerror(scripts.onerror, script_info, e, logger=logger)
                    raise
