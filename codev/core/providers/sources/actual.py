import shutil
from uuid import uuid1

from codev.core.executor import BareExecutor
from codev.core.source import Source


class ActualSource(Source):
    provider_name = 'actual'

    def install(self, executor: BareExecutor) -> None:
        filename = uuid1()
        archive = shutil.make_archive(f'/tmp/{filename}', 'gztar')

        remote_archive = f'/tmp/{filename}.tar.gz'

        executor.send_file(archive, remote_archive)

        # install gunzip
        # TODO requirements
        # executor.install_packages('gzip')

        executor.execute(f'tar -xzf {remote_archive}')
