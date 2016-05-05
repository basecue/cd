from codev.isolator import Isolator


class DirectoryIsolator(Isolator):
    provider_name = 'directory'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_dir = '~/.share/codev/{ident}/directory'.format(ident=self.ident)

    def exists(self):
        return self.performer.check_execute('[ -d {dir} ]'.format(dir=self.base_dir))

    def create(self):
        self.performer.execute('mkdir -p {dir}'.format(dir=self.base_dir))

    def is_started(self):
        return self.exists

    def destroy(self):
        return self.performer.execute('rm -rf {dir}'.format(dir=self.base_dir))

    def execute(self, command, logger=None, writein=None, max_lines=None):
        return super().execute(
            self._prepare_command(command), logger=logger, writein=writein, max_lines=max_lines
        )
