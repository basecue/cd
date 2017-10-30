

def parse_options(inp):
    parsed = inp.split(':', 1)
    name = parsed[0]
    options = parsed[1] if len(parsed) == 2 else ''
    return name, options


class Ident(object):
    def __init__(self, *args):
        self._ident = args

    def as_tuple(self):
        return tuple(filter(None, self._ident))

    def as_directory(self):
        return '_'.join(self.as_tuple())