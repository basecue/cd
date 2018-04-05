from typing import Dict, Any

import ast
import json

from .settings import BaseSettings


class DebugSettings(BaseSettings):
    settings = None
    perform_settings = None

    @property
    def loglevel(self) -> str:
        return self.data.get('loglevel', 'info').lower()

    @property
    def distfile(self) -> str:
        return self.data.get('distfile', '')

    @property
    def ssh_copy(self) -> bool:
        return ast.literal_eval(self.data.get('ssh_copy', 'True'))

    @property
    def show_exception(self) -> bool:
        return ast.literal_eval(self.data.get('show_exception', 'False'))

    @property
    def load_vars(self) -> Dict[str, Any]:
        return json.loads(self.data.get('load_vars', '{}'))

    @property
    def preserve_cache(self) -> bool:
        return ast.literal_eval(self.data.get('preserve_cache', 'False'))


DebugSettings.settings = DebugSettings()
DebugSettings.perform_settings = DebugSettings()
