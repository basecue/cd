from codev.core.provider import Provider, ConfigurableProvider


class Task(Provider, ConfigurableProvider):
    def __init__(self, performer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.performer = performer

    def prepare(self):
        raise NotImplementedError()

    def run(self, infrastructure, script_info, input_vars):
        raise NotImplementedError()

