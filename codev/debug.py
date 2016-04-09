from .settings import BaseSettings
from ast import literal_eval


class DebugSettings(BaseSettings):
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


DebugSettings.configuration = DebugSettings()
DebugSettings.perform_configuration = DebugSettings()
