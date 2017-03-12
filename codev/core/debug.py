from ast import literal_eval
import json

from .settings import BaseSettings


class DebugSettings(BaseSettings):
    settings = None
    perform_settings = None

    @property
    def loglevel(self):
        return self.data.get('loglevel', 'info').lower()

    @property
    def distfile(self):
        return self.data.get('distfile', '')

    @property
    def ssh_copy(self):
        return literal_eval(self.data.get('ssh_copy', 'True'))

    @property
    def show_client_exception(self):
        return literal_eval(self.data.get('show_client_exception', 'True'))

    @property
    def load_vars(self):
        return json.loads(self.data.get('load_vars', '{}'))


DebugSettings.settings = DebugSettings()
DebugSettings.perform_settings = DebugSettings()
