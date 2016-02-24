from .configuration import BaseConfiguration
from ast import literal_eval


class DebugConfiguration(BaseConfiguration):
    configuration = None
    perform_configuration = None

    @property
    def loglevel(self):
        return self.data.get('loglevel', 'info').lower()

    @property
    def distfile(self):
        return self.data.get('distfile', '')

    @property
    def show_client_exception(self):
        return literal_eval(self.data.get('show_client_exception', 'False'))

    @property
    def repository(self):
        return self.data.get('repository', None)

    @property
    def directory(self):
        return self.data.get('directory', None)

DebugConfiguration.configuration = DebugConfiguration()
DebugConfiguration.perform_configuration = DebugConfiguration()
