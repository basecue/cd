# Copyright (C) 2016  Jan Češpivo <jan.cespivo@gmail.com>
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License along
#     with this program; if not, write to the Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from subprocess import Popen, PIPE, call

from threading import Thread

from codev.performer import CommandError, BasePerformer, Performer, OutputReader

from logging import getLogger


class LocalPerformer(BasePerformer):
    def __init__(self, *args, **kwargs):
        super(LocalPerformer, self).__init__(*args, **kwargs)
        self._output_lines = []
        self._error_lines = []
        self.logger = getLogger(__name__)

    def _reader_out(self, stream, logger=None):
        while True:
            line = stream.readline()
            if not line:
                break
            output_line = line.decode('utf-8').strip()
            self._output_lines.append(output_line)
            (logger or self.output_logger).debug(output_line)
        stream.close()

    def execute(self, command, logger=None, writein=None):
        self.logger.debug('Executing LOCAL command: %s' % command)
        self._output_lines = []
        self._error_lines = []
        process = Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell=True)

        # read stdout asynchronously - in 'realtime'
        output_reader = OutputReader(process.stdout, logger=logger or self.output_logger)

        if writein:
            # write writein to stdin
            process.stdin.write(writein.encode())
            process.stdin.close()

        # wait for end of output
        output_reader.output()

        # wait for exit code
        exit_code = process.wait()


        if exit_code:
            # read stderr for error output
            err = process.stderr.read().decode('utf-8').strip()
            raise CommandError(command, exit_code, err)
        return '\n'.join(self._output_lines)

    def send_file(self, source, target):
        call('cp', source, target)


Performer.register('local', LocalPerformer)
