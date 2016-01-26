
class BaseExecutor(object):
    def __init__(self, configuration):
        self.configuration = configuration

"""
maybe move to command line client part
"""
class Executor(BaseExecutor):
    def __init__(self, configuration, executor_class):
        super(Executor, self).__init__(configuration)
        self.executor = executor_class(self.configuration)

    def __getattr__(self, name):
        return getattr(self.executor, name)
"""
"""


class Perform(BaseExecutor):
    def install(self):
        print('perform')


class Control(BaseExecutor):
    def __init__(self, *args, **kwargs):
        super(Control, self).__init__(*args, **kwargs)
        self.performer = self.configuration.current.environment.performer
        self.isolation = self.configuration.current.environment.isolation

    def install(self):
        self.performer.execute(self.isolation(self.configuration).commands)

        #
        # #get or create isolation
        # self.configuration.isolation
        #
        # #install proper version of codev
        # self.configuration.version
        #
        # #copy configuration file
        # self.

