from contextlib import contextmanager
from subprocess import Popen, PIPE, call

from os import fdopen, remove
from os.path import expanduser
from logging import getLogger

from tempfile import mkstemp

from codev.core.executor import Executor, CommandError, OutputReader


class LocalExecutor(Executor):
    provider_name = 'local'

    def __init__(self, *args, **kwargs):
        self.logger = getLogger(__name__)
        super().__init__(*args, **kwargs)

    def execute(self, command):
        self.logger.debug("Execute command: '%s'" % command)

        outtempfd, outtemppath = mkstemp()
        errtempfd, errtemppath = mkstemp()

        with fdopen(outtempfd, 'w+b') as outfile,\
            open(outtemppath, 'r+b') as outfileread,\
            fdopen(errtempfd, 'w+b') as errfile,\
            open(errtemppath, 'r+b') as errfileread:
            process = Popen(str(command), stdout=outfile, stderr=errfile, stdin=PIPE, shell=True)

            if command.writein:
                # write writein to stdin
                process.stdin.write(command.writein.encode())
                process.stdin.flush()
            process.stdin.close()

            output_reader = OutputReader(
                outfileread,
                errfileread,
                logger=command.logger
            )

            # wait for exit code
            exit_code = process.wait()

            # flush data
            outfile.flush()
            errfile.flush()

            output, error = output_reader.output()

        remove(outtemppath)
        remove(errtemppath)

        if exit_code:
            raise CommandError(command, exit_code, error, output)
        return output

    def send_file(self, source, target):
        self.logger.debug("Send file: '{source}' '{target}'".format(source=source, target=target))
        expanduser_source = expanduser(source)
        if expanduser_source != source:
            self.logger.debug(
                "Expanduser: '{source}' -> '{expanduser_source}'".format(
                    source=source, expanduser_source=expanduser_source
                )
            )
        call(['cp', expanduser_source, target])

    @contextmanager
    def get_fo(self, remote_path):
        with open(remote_path) as fo:
            yield fo
