import logging


LOGLEVELS = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
}

actual_loglevel = 'info'


class LoglevelFilter(logging.Filter):
    def __init__(self, loglevel):
        self.loglevel = loglevel
        super().__init__()

    def filter(self, record):
        if record.levelno == self.loglevel:
            return True

error_filter = LoglevelFilter(logging.ERROR)
info_filter = LoglevelFilter(logging.INFO)
debug_filter = LoglevelFilter(logging.DEBUG)
