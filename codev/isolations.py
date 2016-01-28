import re


class LXCIsolation(object):
    def __init__(self, configuration):
        self.configuration = configuration
        self.performer = self.configuration.current.environment.performer
        self.name = '%s_%s_%s_%s' % (
            self.configuration.project,
            self.configuration.current.environment.name,
            self.configuration.current.infrastructure.name,
            self.configuration.current.version
        )
        self._isolate()

    def send_file(self, source, target):
        TMPFILE = 'tempfile'
        self.performer.send_file(source, TMPFILE)
        self.performer.execute('cat %(tmpfile)s | lxc-attach -n %(name)s -- tee %(target)s' % {
            'name': self.name,
            'tmpfile': TMPFILE,
            'target': target
        }, mute=True)
        self.performer.execute('rm -f %(tmpfile)s' % {'tmpfile': TMPFILE})

    def execute(self, command):
        return self.performer.execute('lxc-attach -n %(name)s -- %(command)s' % {
            'name': self.name,
            'command': command
        })

    def _lxc_is_started(self):
        output = self.performer.execute('lxc-info -n %(name)s -s' % {
            'name': self.name
        })

        r = re.match('^State:\s+(.*)$', output.strip())
        if r:
            state = r.group(1)
        else:
            raise ValueError(output)

        if state == 'RUNNING':
            return True
        elif state == 'STOPPED':
            return False
        else:
            raise ValueError(state)

    def _lxc_get_ip(self):
        output = self.performer.execute('lxc-info -n %(name)s' % {
            'name': self.name
        })

        for line in output.splitlines():
            r = re.match('^IP:\s+([0-9\.]+)$', line)
            if r:
                return r.group(1)

        raise ValueError(output)

    def _lxc_create(self):
        self.performer.execute('lxc-create -t download -n %(name)s -- --dist ubuntu --release trusty --arch amd64' % {
            'name': self.name
        })

    def _lxc_start(self):
        self.performer.execute('lxc-start -n %(name)s' % {
            'name': self.name
        })

    def _isolate(self):
        is_started = self._lxc_is_started()

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
