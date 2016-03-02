from .provider import BaseProvider
from codev.performer import BasePerformer, BackgroundRunner


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
