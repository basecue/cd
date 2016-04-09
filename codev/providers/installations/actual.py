from codev.installation import Installation, BaseInstallation
import shutil
from time import time
from uuid import uuid1


class ActualInstallation(BaseInstallation):
    def install(self, performer):
        archive = shutil.make_archive('/tmp/{filename}'.format(filename=uuid1()), 'gztar')
        performer.send_file(archive, archive)
        # install gunzip
        performer.install_packages('gzip')

        performer.execute('mkdir -p {directory}'.format(directory=self.directory))
        performer.execute(
            'tar -xzf {archive} --directory {directory}'.format(
                archive=archive, directory=self.directory
            )
        )

    def process_options(self, options):
        self.uid = options or str(time())

    @property
    def id(self):
        return self.uid

Installation.register('actual', ActualInstallation)
