from codev.installation import Installation, BaseInstallation
import shutil
from time import time


class ActualInstallation(BaseInstallation):
    def install(self, performer):
        # gunzip is in default ubuntu
        # performer.execute('apt-get install gunzip -y --force-yes')
        archive = shutil.make_archive('/tmp/', 'gztar')
        performer.send_file(archive, archive)
        performer.execute('mkdir -p {directory}'.format(directory=self.directory))
        performer.execute('tar -xzf {archive} --directory {directory}'.format(archive=archive, directory=self.directory))

    def process_options(self, options):
        self.uid = options or str(time())

    @property
    def id(self):
        return self.uid

Installation.register('actual', ActualInstallation)
