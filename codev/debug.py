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


DebugConfiguration.configuration = DebugConfiguration()
DebugConfiguration.perform_configuration = DebugConfiguration()
