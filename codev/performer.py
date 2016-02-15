from urllib.parse import urlparse
from .provider import BaseProvider


class PerformerError(Exception):
    pass


class CommandError(PerformerError):
    def __init__(self, command, exit_code, error):
        super(CommandError, self).__init__(
            "Command '{command}' failed with exit code '{exit_code}' with error '{error}'".format(
                command=command, exit_code=exit_code, error=error
            )
        )


class BasePerformer(object):
    pass


class Performer(BaseProvider):
    provider_class = BasePerformer

    def __new__(cls, provider_url, isolation_ident=None):
        parsed_url = urlparse(provider_url)
        provider_name = parsed_url.scheme
        return super(Performer, cls).__new__(cls, provider_name, parsed_url, isolation_ident)