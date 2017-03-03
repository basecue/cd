from logging import getLogger

from codev_core.performer import ScriptExecutor
from codev_core.infrastructure import Infrastructure
from codev_core.debug import DebugSettings

from .isolation import Isolation


logger = getLogger(__name__)


class Configuration(ScriptExecutor):
    def __init__(self, settings, source, next_source=None, **kwargs):
        performer = kwargs['performer']
        self.settings = settings
        self.source = source
        self.next_source = next_source
        self.isolation = Isolation(self.settings.isolation, self.source, self.next_source, performer=performer)
        self.infrastructure = Infrastructure(self.isolation, self.settings.infrastructure)
        super().__init__(performer=self.performer)

    def deploy(self, status, input_vars):
        status.update(self.status)

        input_vars.update(DebugSettings.settings.load_vars)

        self.isolation.install(status)

        return self.isolation.deploy(self.infrastructure, status, input_vars)

    @property
    def status(self):
        """
        Information about configuration (and isolation if exists)
        :return: configuration status
        :rtype: dict
        """
        if self.isolation.exists():
            infrastructure_status = self.infrastructure.status
        else:
            infrastructure_status = {}

        status = dict(
            source=self.source.name,
            source_options=self.source.options,
            source_ident=self.source.ident,
            next_source=self.next_source.name if self.next_source else '',
            next_source_options=self.next_source.options if self.next_source else '',
            next_source_ident=self.next_source.ident if self.next_source else '',
            infrastructure=infrastructure_status,
            isolation=self.isolation.status
        )

        return status

    def destroy(self):
        if self.isolation.exists():
            self.isolation.destroy()
            logger.info('Isolation has been destroyed.')
            return True
        else:
            logger.info('There is no such isolation.')
            return False
