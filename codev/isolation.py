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
    def __init__(self, performer_configuration, isolation_configuration, ident):
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

    def enter(self, create=False):
        if create:
            logger.info("Creating isolation...")
            if self._isolation.create():
                # run oncreate scripts
                self._isolation.run_scripts(self.scripts.oncreate)

        logger.info("Entering isolation...")
        # run onenter scripts
        self._isolation.run_scripts(self.scripts.onenter)
        return self._isolation

    def destroy(self):
        return self._isolation.destroy()