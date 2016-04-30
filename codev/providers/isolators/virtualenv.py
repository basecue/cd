from .directory import DirectoryIsolator
from os import path


class VirtualenvIsolator(DirectoryIsolator):
    provider_name = 'virtualenv'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._env_dir = '~/.share/codev/{ident}/virtualenv'.format(ident=self.ident)

    def exists(self):
        return super().exists() and path.isdir(self._env_dir)

    def create(self):
        super().create()
        self.performer.execute('virtualenv {env_dir}'.format(env_dir=self._env_dir))

    def is_started(self):
        return self.exists

    def destroy(self):
        super().destroy()
        return self.performer.execute('rm -rf {env_dir}'.format(env_dir=self._env_dir))

    def execute(self, command, logger=None, writein=None, max_lines=None):
        super().execute(
            'bash -c "{env_dir}/bin/activate && command"'.format(
                env_dir=self._env_dir,
                command=command.replace('\\', '\\\\').replace('$', '\$').replace('"', '\\"')
            ), logger=None, writein=None, max_lines=None
        )
