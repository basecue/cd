from .provider import BaseProvider
from .performer import BasePerformer, BackgroundRunner
from logging import getLogger

logger = getLogger(__name__)

# TODO what is the difference between isolation and machine?


class BaseIsolation(BasePerformer):
    def __init__(self, performer, *args, **kwargs):
        super(BaseIsolation, self).__init__(*args, **kwargs)
        self.performer = performer

        # TODO refactorize - move to another class (see bellow)
        self.background_runner = BackgroundRunner(self.performer, ident=self.ident)

    def exists(self):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def destroy(self):
        raise NotImplementedError()

    def execute(self, command, logger=None, writein=None):
        raise NotImplementedError()

    @property
    def ip(self):
        raise NotImplementedError()

    # TODO refactorize - move to another class
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
