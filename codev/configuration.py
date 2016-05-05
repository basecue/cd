from logging import getLogger

from .deployment import Deployment

from .infrastructure import Infrastructure
from .isolation import Isolation


logger = getLogger(__name__)
command_logger = getLogger('command')


class Configuration(object):
    def __init__(self, performer, settings, source, next_source=None, disable_isolation=False):
        self.settings = settings
        self.performer = performer
        self.source = source
        self.next_source = next_source
        self.isolation = None

        if disable_isolation:
            if next_source:
                raise ValueError('Next source is not allowed with disabled isolation.')
            self.isolation = None
        else:
            self.isolation = Isolation(self.settings.isolation, self.source, self.next_source, performer)

        self.infrastructure = Infrastructure(performer, self.settings.infrastructure)
        self.deployment = Deployment(performer, self.settings.provision)

    def deploy(self, info):
        info.update(self.info)
        if self.isolation:
            self.isolation.install(info)
            self.isolation.deploy(self.infrastructure, info)
        else:
            logger.info("Deploying project.")
            self.deployment.deploy(self.infrastructure, info)

    def run_script(self, script, arguments=None):
        executor = self.isolation or self.performer

        if arguments is None:
            arguments = {}
        arguments.update(self.info)
        executor.run_script(script, arguments=arguments, logger=command_logger)

    @property
    def info(self):
        """
        Information about configuration (and isolation if exists)
        :return: configuration info
        :rtype: dict
        """
        if not self.isolation or (self.isolation.exists() and self.isolation.is_started()):
            infrastructure_info = self.infrastructure.info
        else:
            infrastructure_info = {}

        info = dict(
            source=self.source.name,
            source_options=self.source.options,
            source_ident=self.source.ident,
            next_source=self.next_source.name if self.next_source else '',
            next_source_options=self.next_source.options if self.next_source else '',
            next_source_ident=self.next_source.ident if self.next_source else '',
            infrastructure=infrastructure_info
        )
        if self.isolation:
            info.update(isolation=self.isolation.info)

        return info

    def destroy(self):
        if self.isolation and self.isolation.exists():
            self.isolation.destroy()
            logger.info('Isolation has been destroyed.')
            return True
        else:
            logger.info('There is no such isolation.')
            return False
