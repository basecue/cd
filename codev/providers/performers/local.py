from contextlib import contextmanager
from subprocess import Popen, PIPE, call
from os.path import expanduser

from codev.performer import CommandError, Performer, OutputReader

from logging import getLogger


class LocalPerformer(Performer):
    provider_name = 'local'

    def __init__(self, *args, **kwargs):
        self.logger = getLogger(__name__)
        super().__init__(*args, **kwargs)

    def execute(self, command, logger=None, writein=None, max_lines=None):
        self.logger.debug("Execute command: '%s'" % command)
        process = Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell=True)

        if writein:
            # write writein to stdin
            process.stdin.write(writein.encode())
            process.stdin.flush()
        process.stdin.close()

        # read stdout asynchronously - in 'realtime'
        output_reader = OutputReader(process.stdout, logger=logger or self.output_logger, max_lines=max_lines)

        # wait for end of output
        output = output_reader.output()

        # wait for exit code
        exit_code = process.wait()

        if exit_code:
            err = process.stderr.read().decode('utf-8').strip()
            raise CommandError(command, exit_code, err)
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
