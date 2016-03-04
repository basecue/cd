from .provider import BaseProvider
from .performer import BasePerformer, BackgroundRunner
from logging import getLogger

logger = getLogger(__name__)


class BaseIsolation(BasePerformer):
    def __init__(self, performer, *args, **kwargs):
        super(BaseIsolation, self).__init__(*args, **kwargs)
        self.performer = performer
        self.background_runner = BackgroundRunner(self.performer, ident=self.ident)

    def exists(self):
        raise NotImplementedError()

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

    @property
    def ip(self):
        raise NotImplementedError()


class Isolation(BaseProvider):
    provider_class = BaseIsolation


# class IsolationProvider(object):
#     def __init__(self,
#                  project_name,
#                  environment_name,
#                  infrastructure_name,
#                  performer,
#                  isolation_configuration,
#                  installation,
#                  next_installation=None
#                  ):
#
#         ident = '%s:%s:%s:%s' % (
#             project_name,
#             environment_name,
#             infrastructure_name,
#             installation.ident,
#         )
#
#         if next_installation:
#             ident = '%s:%s' % (ident, next_installation.ident)
#
#         self.installation = installation
#         self.next_installation = next_installation
#         self.current_installation = None
#
#         self._isolation = Isolation(
#             isolation_configuration.provider,
#             performer,
#             ident=md5(ident.encode()).hexdigest()
#         )
#         self.scripts = isolation_configuration.scripts
#
#     def enter(self, create=False, next_install=False):
#         # TODO move to deployment
#         if create:
#             logger.info("Creating isolation...")
#             if self._isolation.create():
#                 logger.info("Install project to isolation.")
#                 self.current_installation = self.installation
#                 self.current_installation.install(self._isolation)
#
#                 # run oncreate scripts
#                 with self._isolation.directory(self.current_installation.directory):
#                     self._isolation.run_scripts(self.scripts.oncreate)
#             else:
#                 if next_install and self.next_installation:
#                     logger.info("Transition installation in isolation.")
#                     self.current_installation = self.next_installation
#                     self.current_installation.install(self._isolation)
#
#         logger.info("Entering isolation...")
#         # run onenter scripts
#         with self._isolation.directory(self.current_installation.directory):
#             self._isolation.run_scripts(self.scripts.onenter)
#
#         return self._isolation, self.current_installation
#
#     def destroy_isolation(self):
#         # TODO move to deployment
#         return self._isolation.destroy()
