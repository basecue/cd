from codev.source import Source, BaseSource
import shutil
from time import time
from uuid import uuid1


class ActualSource(BaseSource):
    def install(self, performer):
        archive = shutil.make_archive('/tmp/{filename}'.format(filename=uuid1()), 'gztar')

        remote_archive = '/tmp/{filename}.tar.gz'
        performer.send_file(archive, remote_archive)

        # install gunzip
        performer.install_packages('gzip')

        performer.execute('mkdir -p {directory}'.format(directory=self.directory))
        performer.execute(
            'tar -xzf {archive} --directory {directory}'.format(
                archive=remote_archive, directory=self.directory
            )
        )

    def process_options(self, options):
        self.uid = options or str(time())

    @property
    def id(self):
        return self.uid

Source.register('actual', ActualSource)
