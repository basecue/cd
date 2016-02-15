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
    def __init__(self, *args, isolation_ident=None, **kwargs):
        self.isolation_ident = isolation_ident
        super(BasePerformer, self).__init__(*args, **kwargs)


class Performer(BaseProvider):
    provider_class = BasePerformer
