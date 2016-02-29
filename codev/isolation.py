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

from .provider import BaseProvider
from codev.performer import BasePerformer, BackgroundRunner


class BaseIsolation(BasePerformer):
    def __init__(self, performer, ident, *args, **kwargs):
        self.performer = performer
        self.background_runner = BackgroundRunner(self.performer, ident)
        self.ident = ident
        super(BaseIsolation, self).__init__(*args, **kwargs)

    def create(self):
        raise NotImplementedError()

    def destroy(self):
        raise NotImplementedError()

    def execute(self, command, logger=None, writein=None):
        raise NotImplementedError()

    def background_execute(self, command, logger=None, writein=None):
        raise NotImplementedError()

    def background_join(self, logger=None):
        return self.background_runner.join(logger=logger)

    def background_stop(self):
        return self.background_runner.stop()

    def background_kill(self):
        return self.background_runner.kill()


class Isolation(BaseProvider):
    provider_class = BaseIsolation
