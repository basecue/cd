from .provider import BaseProvider, ConfigurableProvider
from .performer import CommandError
from logging import getLogger


class BaseProvisioner(ConfigurableProvider):
    def __init__(self, scripts, performer, configuration, *args, **kwargs):
        self.scripts = scripts
        self.performer = performer
        self.configuration = configuration
        self.logger = getLogger(__name__)
        super(BaseProvisioner, self).__init__(*args, **kwargs)

    def install(self):
        raise NotImplementedError()

    def run(self, machines):
        raise NotImplementedError()

    def _onerror(self, arguments, error):
        self.logger.error(error)
        arguments.update(
            dict(
                command=error.command,
                exit_code=error.exit_code,
                error=error.error
            )
        )
        self.performer.run_scripts(self.scripts.onerror, arguments)

    def provision(self, deployment_info):
        self.performer.run_scripts(self.scripts.onstart, deployment_info)
        try:
            self.logger.info('Installing provisioner...')
            self.install()

            self.logger.info('Creating machines...')
            machines_groups = self.configuration.machines_groups(self.performer, create=True)

            self.logger.info('Configuration...')
            self.run(machines_groups)
        except CommandError as e:
            self._onerror(deployment_info, e)
            return False
        else:
            try:
                arguments = {}
                arguments.update(deployment_info)
                arguments.update(self.configuration.machines_info(self.performer))
                self.performer.run_scripts(self.scripts.onsuccess, arguments)
                return True
            except CommandError as e:
                self._onerror(deployment_info, e)
                return False


class Provisioner(BaseProvider):
    provider_class = BaseProvisioner
