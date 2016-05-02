from codev.isolator import Isolator


class DirectoryIsolator(Isolator):
    provider_name = 'directory'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dir = '~/.share/codev/{ident}'.format(ident=self.ident)

    def exists(self):
        return self.performer.check_execute('[ -d {dir} ]'.format(dir=self._dir))

    def create(self):
        self.performer.execute('mkdir -p {dir}'.format(dir=self._dir))
        return True

    def is_started(self):
        return self.exists

    def destroy(self):
        return self.performer.execute('rm -rf {dir}'.format(dir=self._dir))

    def execute(self, command, logger=None, writein=None, max_lines=None):
        with self.performer.change_directory(self._dir):
            return super().execute(
                'bash -c "cd {working_dir} && {command}"'.format(
                    working_dir=self.performer.working_dir,
                    command=command.replace('\\', '\\\\').replace('$', '\$').replace('"', '\\"')
                ), logger=None, writein=None, max_lines=None
            )
