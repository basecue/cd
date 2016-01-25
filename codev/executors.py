

class Execution(object):
    def __init__(self, configuration, environment, infrastructure, version):
        self.configuration = configuration
        self.environment = environment
        self.infrastructure = infrastructure
        self.version = version

    def install(self):
        pass


class Perform(Execution):
    def install(self):
        print('perform')


class Control(Execution):
    def install(self):
        print('control')
        #connect to performer
        # self.configuration.performer
        #
        # #get or create isolation
        # self.configuration.isolation
        #
        # #install proper version of codev
        # self.configuration.version
        #
        # #copy configuration file
        # self.

