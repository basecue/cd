from codev.isolator import Isolator
from os import path


class DirectoryIsolator(Isolator):
    provider_name = 'directory'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dir = '~/.share/codev/{ident}/directory'.format(ident=self.ident)

    def exists(self):
        return path.isdir(self._dir)

    def create(self):
        self.performer.execute('mkdir -p {dir}'.format(dir=self._dir))

    def is_started(self):
        return self.exists

    def destroy(self):
        return self.performer.execute('rm -rf {dir}'.format(env_dir=self._dir))

    def execute(self, command, logger=None, writein=None, max_lines=None):
        with self.performer.change_directory(self._dir):
            super().execute(command, logger=None, writein=None, max_lines=None)
