from logging import getLogger

from .deployment import Deployment

from .infrastructure import Infrastructure
from .isolation import Isolation
from .performer import CommandError, ScriptExecutor, ProxyPerformer

logger = getLogger(__name__)


class Configuration(ScriptExecutor):
    def __init__(self, settings, source, next_source=None, disable_isolation=False, **kwargs):
        performer = kwargs.get('performer')  # required
        self.settings = settings
        self.source = source
        self.next_source = next_source

        if disable_isolation:
            if next_source:
                raise ValueError('Next source is not allowed with disabled isolation.')
            self.isolation = None
        else:
            self.isolation = Isolation(self.settings.isolation, self.source, self.next_source, performer=performer)

        self.performer = self.isolation or performer

        self.infrastructure = Infrastructure(performer, self.settings.infrastructure)
        super().__init__(performer=self.performer)

    def deploy(self, info, vars):
        info.update(self.info)

        if self.isolation:

            self.isolation.install(info)

            return self.isolation.deploy(self.infrastructure, info, vars)
        else:
            logger.info("Deploying project.")

            scripts = self.settings.scripts

            try:
                self.execute_scripts(scripts.onstart, info)

                deployment = Deployment(self.settings.provisions, performer=self.performer)
                deployment.deploy(self.infrastructure, info, vars)

            except CommandError as e:
                self.execute_scripts_onerror(scripts.onerror, info, e, logger=logger)
                return False
            else:
                try:
                    self.execute_scripts(scripts.onsuccess, info)
                    return True
                except CommandError as e:
                    self.execute_scripts_onerror(scripts.onerror, info, e, logger=logger)
                    return False

    def execute_script(self, script, arguments=None, logger=None):
        if arguments is None:
            arguments = {}

        arguments.update(self.info)
        return super().execute_script(script, arguments=arguments, logger=arguments)

    @property
    def info(self):
        """
        Information about configuration (and isolation if exists)
        :return: configuration info
        :rtype: dict
        """
        if not self.isolation or self.isolation.exists():
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
