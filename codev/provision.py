from .provider import BaseProvider, ConfigurableProvider
from .performer import CommandError
from logging import getLogger


class BaseProvisioner(ConfigurableProvider):
    def __init__(self, scripts, performer, infrastructure, *args, **kwargs):
        self.scripts = scripts
        self.performer = performer
        self.infrastructure = infrastructure
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
            machines_groups = self.infrastructure.machines_groups(self.performer, create=True)

            self.logger.info('Starting provisioning...')
            self.run(machines_groups)
        except CommandError as e:
            self._onerror(deployment_info, e)
            return False
        else:
            try:
                self.performer.run_scripts(self.scripts.onsuccess, deployment_info)
                return True
            except CommandError as e:
                self._onerror(deployment_info, e)
                return False


class Provisioner(BaseProvider):
    provider_class = BaseProvisioner
