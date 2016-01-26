class LXCIsolation(object):
    def __init__(self, configuration):
        self.configuration = configuration
        self.name = '%s_%s_%s_%s' % (
            self.configuration.project,
            self.configuration.current.environment.name,
            self.configuration.current.infrastructure.name,
            self.configuration.current.version
        )

    @property
    def commands(self):
        """
        TODO make this idempotent
        """
        yield 'lxc-create -t download -n %(name)s -- --dist ubuntu --release trusty --arch amd64' % {
            'name': self.name
        }
        yield 'lxc-start -n %(name)s' % {
            'name': self.name
        }
        # yield 'lxc-attach -n %(name)s -- apt-get update' % {
        #     'name': self.name
        # }
        # yield 'lxc-attach -n %(name)s -- apt-get install lxc -y' % {
        #     'name': self.name
        # }

ISOLATIONS = {
    'lxc': LXCIsolation
}


class Isolation(object):
    def __new__(cls, ident):
        return ISOLATIONS[ident]
