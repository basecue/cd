from .provider import BaseProvider
from .performer import Performer, BasePerformer, BackgroundRunner
from logging import getLogger
from hashlib import md5

logger = getLogger(__name__)


class BaseIsolation(BasePerformer):
    def __init__(self, performer, *args, **kwargs):
        super(BaseIsolation, self).__init__(*args, **kwargs)
        self.performer = performer
        self.background_runner = BackgroundRunner(self.performer, ident=self.ident)

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
                 installation,
                 next_installation=None
                 ):

        ident = '%s:%s:%s:%s' % (
            project_name,
            environment_name,
            infrastructure_name,
            installation.ident,
        )

        if next_installation:
            ident = '%s:%s' % (ident, next_installation.ident)

        self.installation = installation
        self.next_installation = next_installation

        performer = Performer(
            performer_configuration.provider,
            configuration_data=performer_configuration.specific
        )

        self._isolation = Isolation(
            isolation_configuration.provider,
            performer,
            ident=md5(ident.encode()).hexdigest()
        )
        self.scripts = isolation_configuration.scripts

    def enter(self, create=False, next_install=False):
        directory = '{base_dir}/repository'.format(base_dir=self._isolation.base_dir)
        if create:
            logger.info("Creating isolation...")
            if self._isolation.create():
                logger.info("Install project to isolation.")
                self.installation.install(self._isolation, directory)

                # run oncreate scripts
                self._isolation.base_dir = directory
                self._isolation.run_scripts(self.scripts.oncreate)
            else:
                if next_install and self.next_installation:
                    logger.info("Transition installation in isolation.")
                    self.next_installation.install(self._isolation, directory)

        self._isolation.base_dir = directory

        logger.info("Entering isolation...")
        # run onenter scripts
        self._isolation.run_scripts(self.scripts.onenter)
        return self._isolation

    def destroy(self):
        return self._isolation.destroy()
