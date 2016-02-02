import re
from .performers import Performer


class LXCIsolation(object):
    def __init__(self, performer, ident):
        self.performer = performer
        self.ident = ident
        self._isolate()

    def send_file(self, source, target):
        TMPFILE = 'tempfile'
        self.performer.send_file(source, TMPFILE)
        self.performer.execute('cat %(tmpfile)s | lxc-attach -n %(name)s -- tee %(target)s' % {
            'name': self.ident,
            'tmpfile': TMPFILE,
            'target': target
        }, mute=True)
        self.performer.execute('rm -f %(tmpfile)s' % {'tmpfile': TMPFILE})

    def execute(self, command):
        return self.performer.execute('lxc-attach -n %(name)s -- %(command)s' % {
            'name': self.ident,
            'command': command
        })

    def _lxc_is_started(self):
        output = self.performer.execute('lxc-info -n %(name)s -s' % {
            'name': self.ident
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
            'name': self.ident
        })

        for line in output.splitlines():
            r = re.match('^IP:\s+([0-9\.]+)$', line)
            if r:
                return r.group(1)

        raise ValueError(output)

    def _lxc_create(self, distribution, release):
        architecture = self.performer.execute('uname -m')
        if architecture == 'x86_64':
            architecture = 'amd64'
        self.performer.execute('lxc-create -t download -n %(name)s -- --dist %(distribution)s --release %(release)s --arch %(architecture)s' % {
            'name': self.ident,
            'distribution': distribution,
            'release': release,
            'architecture': architecture
        })

    def _lxc_start(self):
        self.performer.execute('lxc-start -n %(name)s' % {
            'name': self.ident
        })

    def _isolate(self):
        is_started = self._lxc_is_started()

        if is_started is None:
            self._lxc_create('ubuntu', 'trusty')

        elif not is_started:
            self._lxc_start()

        # yield 'lxc-attach -n %(name)s -- apt-get update' % {
        #     'name': self.name
        # }
        # yield 'lxc-attach -n %(name)s -- apt-get install lxc -y' % {
        #     'name': self.name
        # }

LXC_ISOLATION = 'lxc'

ISOLATION_BY_NAME = {
    LXC_ISOLATION: LXCIsolation
}

DEFAULT_ISOLATION = LXC_ISOLATION


class Isolation(object):
    def __init__(self, isolation_name, performer_ident):
        self.performer = Performer(performer_ident)
        self.isolation_class = ISOLATION_BY_NAME[isolation_name]

    def __call__(self, isolation_ident):
        return self.isolation_class(self.performer, isolation_ident)


