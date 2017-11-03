from contextlib import contextmanager
import shutil
from time import time
from uuid import uuid1

from codev.core.source import Source


class ActualSource(Source):
    provider_name = 'actual'

    def __init__(self, options, *args, **kwargs):
        options = options or str(time())
        super().__init__(options, *args, **kwargs)

    def install(self):
        filename = uuid1()
        archive = shutil.make_archive('/tmp/{filename}'.format(filename=filename), 'gztar')

        remote_archive = '/tmp/{filename}.tar.gz'.format(filename=filename)

        self.executor.send_file(archive, remote_archive)

        # install gunzip
        # TODO requirements
        # executor.install_packages('gzip')

        self.executor.execute(
            'tar -xzf {archive}'.format(
                archive=remote_archive
            )
        )
