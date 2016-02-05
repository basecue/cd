import re


class Machine(object):
    @property
    def ip(self):
        raise NotImplementedError()


class LXCMachine(Machine):
    def __init__(self, perfomer, ident, distribution, release, architecture):
        self.performer = perfomer
        self.ident = ident
        self.distribution = distribution
        self.release = release
        self.architecture = architecture

    def exists(self):
        output = self.performer.execute('lxc-ls')
        return self.ident in output.split()

    def is_started(self):
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

    def create(self):
        if not self.exists():
            self.performer.execute('lxc-create -t download -n %(name)s -- --dist %(distribution)s --release %(release)s --arch %(architecture)s' % {
                'name': self.ident,
                'distribution': self.distribution,
                'release': self.release,
                'architecture': self.architecture
            })
            return True
        else:
            return False

    def start(self):
        if not self.is_started():
            self.performer.execute('lxc-start -n %(name)s' % {
                'name': self.ident
            })
            return True
        else:
            return False

    @property
    def ip(self):
        output = self.performer.execute('lxc-info -n %(name)s -i' % {
            'name': self.ident
        })

        for line in output.splitlines():
            r = re.match('^IP:\s+([0-9\.]+)$', line)
            if r:
                return r.group(1)

        return None

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
