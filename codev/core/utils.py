from typing import Tuple, TypeVar, Union, Optional


def parse_options(inp: str) -> Tuple[str, str]:
    parsed = inp.split(':', 1)
    name = parsed[0]
    options = parsed[1] if len(parsed) == 2 else ''
    return name, options


class Ident(object):
    def __init__(self, *args) -> None:
        self._ident = args

    def as_tuple(self) -> Tuple:
        return tuple(filter(None, self._ident))

    def as_str_tuple(self) -> Tuple:
        return tuple(map(str, self.as_tuple()))

    def as_file(self) -> str:
        return '_'.join(self.as_str_tuple()).replace('/', '-')

    def as_hostname(self) -> str:
        return '-'.join(self.as_str_tuple()).replace('/', '-').replace('_', '-')

    def __str__(self) -> str:
        return str(self.as_tuple())


class HasIdent(object):
    def __init__(self, *args, ident: Optional[Ident] = None, **kwargs) -> None:
        self.ident = ident
        super().__init__(*args, **kwargs)


StatusType = TypeVar('Status', bound='Status')


class Status(dict):
    def __getattr__(self, item: str) -> Union[StatusType, str]:
        return self[item]
