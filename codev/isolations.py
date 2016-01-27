import re


class LXCIsolation(object):
    def __init__(self, configuration):
        self.configuration = configuration
        self.performer_execute = self.configuration.current.environment.performer.execute
        self.name = '%s_%s_%s_%s' % (
            self.configuration.project,
            self.configuration.current.environment.name,
            self.configuration.current.infrastructure.name,
            self.configuration.current.version
        )
        self._isolate()

    def execute(self, command):
        self.performer_execute('lxc-attach -n %(name)s -- %(command)s' % {
            'name': self.name,
            'command': command
        })

    def _lxc_info(self):
        output, errors = self.performer_execute('lxc-info -n %(name)s' % {
            'name': self.name
        })

        if errors:
            raise ValueError(errors)

        state = ''
        ip = ''
        for line in output.splitlines():
            r = re.match('^State:\s+(.*)$', line)
            if r:
                state = r.group(1)

            r = re.match('^IP:\s+([0-9\.]+)$', line)
            if r:
                ip = r.group(1)
                break

        is_started = None
        if state == 'RUNNING':
            is_started = True
        elif state == 'STOPPED':
            is_started = False

        return is_started, ip

    def _lxc_create(self):
        output, errors = self.performer_execute('lxc-create -t download -n %(name)s -- --dist ubuntu --release trusty --arch amd64' % {
            'name': self.name
        })

    def _lxc_start(self):
        output, errors = self.performer_execute('lxc-start -n %(name)s' % {
            'name': self.name
        })

    def _isolate(self):
        is_started, ip = self._lxc_info()

        if is_started is None:
            self._lxc_create()
        elif not is_started:
            self._lxc_start()

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
