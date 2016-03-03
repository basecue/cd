from .installation import Installation
from .provider import BaseProvider
from .performer import Performer, BasePerformer, BackgroundRunner
from logging import getLogger

logger = getLogger(__name__)


class BaseIsolation(BasePerformer):
    def __init__(self, performer, ident, *args, **kwargs):
        self.performer = performer
        self.background_runner = BackgroundRunner(self.performer, ident)
        self.ident = ident
        super(BaseIsolation, self).__init__(*args, **kwargs)

    def create(self):
        raise NotImplementedError()

    def destroy(self):
        raise NotImplementedError()

    def execute(self, command, logger=None, writein=None):
        raise NotImplementedError()

    def background_execute(self, command, logger=None, writein=None):
        raise NotImplementedError()

    def background_join(self, logger=None):
        return self.background_runner.join(logger=logger)

    def background_stop(self):
        return self.background_runner.stop()

    def background_kill(self):
        return self.background_runner.kill()


class Isolation(BaseProvider):
    provider_class = BaseIsolation


class IsolationProvider(object):
    def __init__(self,
                 project_name,
                 environment_name,
                 infrastructure_name,
                 performer_configuration,
                 isolation_configuration,
                 installation_name,
                 installation_options,
                 installation_configuration
                 ):

        self.installation = Installation(
            installation_name,
            installation_options,
            configuration_data=installation_configuration
        )

        ident = '%s_%s_%s_%s_%s' % (
            project_name,
            environment_name,
            infrastructure_name,
            installation_name,
            self.installation.ident
        )

        performer = Performer(
            performer_configuration.provider,
            configuration_data=performer_configuration.specific
        )

        self._isolation = Isolation(
            isolation_configuration.provider,
            performer,
            ident
        )
        self.scripts = isolation_configuration.scripts
        self.directory = None

    def enter(self, create=False):
        if create:
            logger.info("Creating isolation...")
            if self._isolation.create():
                logger.info("Install project 1 to isolation.")
                self.directory = self.installation.install(self._isolation)

                # run oncreate scripts
                self._isolation.run_scripts(self.scripts.oncreate)
            else:
                logger.info("Install project 2 to isolation.")
                self.directory = self.installation.install(self._isolation)

        logger.info("Entering isolation...")
        # run onenter scripts
        self._isolation.run_scripts(self.scripts.onenter)
        return self._isolation

    def destroy(self):
        return self._isolation.destroy()
