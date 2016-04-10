import re
from .provider import BaseProvider
from .performer import BaseRunner, BasePerformer, CommandError
from .debug import DebugSettings
from .settings import YAMLSettingsReader
from logging import getLogger
from .logging import logging_config

logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')


class IsolatorError(Exception):
    pass


class BaseIsolator(BaseRunner, BasePerformer):
    def exists(self):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def destroy(self):
        raise NotImplementedError()

    def make_link(self, source, target):
        # experimental
        raise NotImplementedError()

    @property
    def ip(self):
        raise NotImplementedError()


class Isolator(BaseProvider):
    provider_class = BaseIsolator
