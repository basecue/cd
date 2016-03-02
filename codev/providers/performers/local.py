from subprocess import Popen, PIPE, call

from codev.performer import CommandError, BasePerformer, Performer, OutputReader

from logging import getLogger


class LocalPerformer(BasePerformer):
    def __init__(self, *args, **kwargs):
        super(LocalPerformer, self).__init__(*args, **kwargs)
        self.logger = getLogger(__name__)

    def execute(self, command, logger=None, writein=None):
        self.logger.debug('Executing LOCAL command: %s' % command)
        process = Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell=True)

        # read stdout asynchronously - in 'realtime'
        output_reader = OutputReader(process.stdout, logger=logger or self.output_logger)

        if writein:
            # write writein to stdin
            process.stdin.write(writein.encode())
            process.stdin.close()

        # wait for end of output
        output = output_reader.output()

        # wait for exit code
        exit_code = process.wait()

        if exit_code:
            # read stderr for error output
            err = process.stderr.read().decode('utf-8').strip()
            raise CommandError(command, exit_code, err)
        return output

    def send_file(self, source, target):
        call('cp', source, target)


Performer.register('local', LocalPerformer)
