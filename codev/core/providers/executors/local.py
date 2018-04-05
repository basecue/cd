from typing import IO, Tuple

import contextlib
import multiprocessing.pool
import logging
import os
import os.path
import subprocess
import tempfile
import time

from codev.core.executor import Executor, CommandError, Command

logger = logging.getLogger(__name__)
command_output_logger = logging.getLogger('command_output')


class LocalExecutor(Executor):
    provider_name = 'local'

    def execute_command(self, command: Command) -> str:
        logger.debug(f"Execute command: '{command}'")

        outtempfd, outtemppath = tempfile.mkstemp()
        errtempfd, errtemppath = tempfile.mkstemp()

        with os.fdopen(outtempfd, 'w+b') as outfile, \
                open(outtemppath, 'r+b') as outfileread, \
                os.fdopen(errtempfd, 'w+b') as errfile, \
                open(errtemppath, 'r+b') as errfileread:
            process = subprocess.Popen(str(command), stdout=outfile, stderr=errfile, stdin=subprocess.PIPE, shell=True)

            if command.writein:
                # write writein to stdin
                process.stdin.write(command.writein.encode())
                process.stdin.flush()
            process.stdin.close()

            output_reader = OutputReader(
                outfileread,
                errfileread,
                output_logger=command.output_logger
            )

            # wait for exit code
            exit_code = process.wait()

            # flush data
            outfile.flush()
            errfile.flush()

            output, error = output_reader.output()

        os.remove(outtemppath)
        os.remove(errtemppath)

        if exit_code:
            raise CommandError(command, exit_code, error, output)
        return output

    def send_file(self, source: str, target: str) -> None:
        if source == target:
            return

        subprocess.check_call(['cp', source, target])

    @contextlib.contextmanager
    def open_file(self, remote_path: str) -> IO:
        remote_path = os.path.expanduser(remote_path)
        with open(remote_path) as fo:
            yield fo


class OutputReader(object):
    thread_pool = multiprocessing.pool.ThreadPool(processes=2)

    def __init__(self, stdout, stderr, output_logger=None):
        self._stdout_output = []
        self._stderr_output = []

        self.terminated = False

        self._stdout_reader = self.thread_pool.apply_async(
            self._reader,
            args=(stdout,),
            kwds=dict(output_logger=output_logger)
        )

        self._stderr_reader = self.thread_pool.apply_async(
            self._reader,
            args=(stderr,)
        )

    def _reader(self, output, output_logger=None) -> str:
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

                time.sleep(0.1)
                continue

            for line in lines:
                output_line = line.decode('utf-8').rstrip('\n')
                output_lines.append(output_line)
                if output_logger:
                    output_logger.info(output_line)
                command_output_logger.debug(output_line)

        return '\n'.join(output_lines)

    def output(self) -> Tuple[str, str]:
        self.terminated = True
        return self._stdout_reader.get(), self._stderr_reader.get()
