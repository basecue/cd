from .configuration import BaseConfiguration


class DebugConfiguration(BaseConfiguration):
    configuration = None

    @property
    def loglevel(self):
        return self.data.get('loglevel', 'info').lower()

    @property
    def distfile(self):
        return self.data.get('distfile', '')

    @property
    def perform_command_output(self):
        return bool(self.data.get('perform_command_output', False))

    @property
    def show_client_exception(self):
        return bool(self.data.get('show_client_exception', False))

    @property
    def repository(self):
        return self.data.get('repository', None)

    @property
    def directory(self):
        return self.data.get('directory', None)

DebugConfiguration.configuration = DebugConfiguration()
