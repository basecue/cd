import shutil
from uuid import uuid1

from codev.core.source import Source


class ActualSource(Source):
    provider_name = 'actual'

    def install(self, executor):
        filename = uuid1()
        archive = shutil.make_archive('/tmp/{filename}'.format(filename=filename), 'gztar')

        remote_archive = '/tmp/{filename}.tar.gz'.format(filename=filename)

        executor.send_file(archive, remote_archive)

        # install gunzip
        # TODO requirements
        # executor.install_packages('gzip')

        executor.execute(
            'tar -xzf {archive}'.format(
                archive=remote_archive
            )
        )
