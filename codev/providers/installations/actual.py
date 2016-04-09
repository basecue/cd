from codev.installation import Installation, BaseInstallation
import shutil
from time import time
from uuid import uuid1


class ActualInstallation(BaseInstallation):
    def install(self, performer):
        archive = shutil.make_archive('/tmp/{filename}'.format(filename=uuid1()), 'gztar')

        # dont use tmp dir, sometimes during the boot tmp is cleaned
        remote_archive = '{filename}.tar.gz'
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

Installation.register('actual', ActualInstallation)
