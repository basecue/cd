from contextlib import contextmanager
from multiprocessing.pool import ThreadPool
from subprocess import Popen, PIPE, check_call

from os import fdopen, remove
from os.path import expanduser

from tempfile import mkstemp
from time import sleep

from codev.core.executor import Executor, CommandError


class LocalExecutor(Executor):
    provider_name = 'local'

    def execute_command(self, command):
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
        if source == target:
            return

        check_call(['cp', source, target])

    @contextmanager
    def open_file(self, remote_path):
        remote_path = expanduser(remote_path)
        with open(remote_path) as fo:
            yield fo


class OutputReader(object):
    thread_pool = ThreadPool(processes=2)

    def __init__(self, stdout, stderr, logger=None):
        self._stdout_output = []
        self._stderr_output = []

        self.terminated = False

        self._stdout_reader = self.thread_pool.apply_async(
            self._reader,
            args=(stdout,),
            kwds=dict(logger=logger)
        )

        self._stderr_reader = self.thread_pool.apply_async(
            self._reader,
            args=(stderr,)
        )

    def _reader(self, output, logger=None):
        output_lines = []
        while True:
            try:
                if self.terminated:
                    output.flush()

                lines = output.readlines()
            except ValueError:  # closed file
                break

            if not lines:
                if self.terminated:
                    break

                sleep(0.1)
                continue

            for line in lines:
                output_line = line.decode('utf-8').rstrip('\n')
                output_lines.append(output_line)
                if logger:
                    logger.debug(output_line)

        return '\n'.join(output_lines)

    def output(self):
        self.terminated = True
        return self._stdout_reader.get(), self._stderr_reader.get()



