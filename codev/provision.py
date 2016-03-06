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

    def provision(self):
        self.performer.run_scripts(self.scripts.onstart)
        try:
            self.logger.info('Installing provisioner...')
            self.install()

            self.logger.info('Creating machines...')
            machines_groups = self.infrastructure.machines_groups(self.performer, create=True)

            self.logger.info('Starting provisioning...')
            self.run(machines_groups)
        except CommandError as e:
            self.logger.error(e)
            self.performer.run_scripts(
                self.scripts.onerror,
                dict(
                    command=e.command,
                    exit_code=e.exit_code,
                    error=e.error
                )
            )
            return False
        else:
            self.performer.run_scripts(self.scripts.onsuccess)
            return True


class Provisioner(BaseProvider):
    provider_class = BaseProvisioner
