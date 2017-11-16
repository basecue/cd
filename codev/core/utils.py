from functools import wraps


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

    def as_str_tuple(self):
        return tuple(map(str, self.as_tuple()))

    def as_file(self):
        return '_'.join(self.as_str_tuple()).replace('/', '-')

    def as_hostname(self):
        return '-'.join(self.as_str_tuple()).replace('/', '-').replace('_', '-')

    def __str__(self):
        return self.as_tuple()


class HasIdent(object):
    def __init__(self, *args, ident=None, **kwargs):
        assert isinstance(ident, Ident)
        self.ident = ident
        super().__init__(*args, **kwargs)


class Status(dict):
    def __getattr__(self, item):
        return self[item]


def status(method):
    cls_name = '_'.join(method.__qualname__.split('.'))
    cls = type(cls_name, (Status,), {})

    @wraps(method)
    def wrapper(*args, **kwargs):
        return cls(method(*args, **kwargs))

    return wrapper

