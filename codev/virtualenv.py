import os
import os.path
from subprocess import Popen, PIPE
import sys
from threading import Thread
from urllib.parse import urlparse
from urllib.request import urlretrieve
from venv import EnvBuilder


class CodevEnvBuilder(EnvBuilder):
    """
    This builder installs setuptools and pip so that you can pip or
    easy_install other packages into the created environment.

    :param nodist: If True, setuptools and pip are not installed into the
                   created environment.
    :param nopip: If True, pip is not installed into the created
                  environment.
    :param progress: If setuptools or pip are installed, the progress of the
                     installation can be monitored by passing a progress
                     callable. If specified, it is called with two
                     arguments: a string indicating some progress, and a
                     context indicating where the string is coming from.
                     The context argument can have one of three values:
                     'main', indicating that it is called from virtualize()
                     itself, and 'stdout' and 'stderr', which are obtained
                     by reading lines from the output streams of a subprocess
                     which is used to install the app.

                     If a callable is not specified, default progress
                     information is output to sys.stderr.
    """

    def __init__(self, version, *args, **kwargs):
        self.version = version
        super().__init__(*args, **kwargs)

    def post_setup(self, context):
        """
        Set up any packages which need to be pre-installed into the
        environment being created.

        :param context: The information for the environment creation request
                        being processed.
        """
        os.environ['VIRTUAL_ENV'] = context.env_dir
        # if not self.nodist:
        #     self.install_setuptools(context)
        # # Can't install pip without setuptools
        # if not self.nopip and not self.nodist:
        #     self.install_pip(context)
        self.install_codev(context)
        self.run_codev()

    def reader(self, stream, context):
        """
        Read lines from a subprocess' output stream and either pass to a progress
        callable (if specified) or write progress information to sys.stderr.
        """
        progress = self.progress
        while True:
            s = stream.readline()
            if not s:
                break
            if progress is not None:
                progress(s, context)
            else:
                if not self.verbose:
                    sys.stderr.write('.')
                else:
                    sys.stderr.write(s.decode('utf-8'))
                sys.stderr.flush()
        stream.close()

    def install_via_pip(self, context, name):
        # _, _, path, _, _, _ = urlparse(url)
        binpath = context.bin_path
        # distpath = os.path.join(binpath, fn)
        # # Download script into the env's binaries folder
        # urlretrieve(url, distpath)
        # progress = self.progress
        # if self.verbose:
        #     term = '\n'
        # else:
        #     term = ''
        # if progress is not None:
        #      progress('Installing %s ...%s' % (name, term), 'main')
        # else:
        #     sys.stderr.write('Installing %s ...%s' % (name, term))
        #     sys.stderr.flush()
        # Install in the env
        args = [context.env_exe, 'pip', 'install', name]
        p = Popen(args, stdout=PIPE, stderr=PIPE, cwd=binpath)
        t1 = Thread(target=self.reader, args=(p.stdout, 'stdout'))
        t1.start()
        t2 = Thread(target=self.reader, args=(p.stderr, 'stderr'))
        t2.start()
        p.wait()
        t1.join()
        t2.join()
        # if progress is not None:
        #     progress('done.', 'main')
        # else:
        #     sys.stderr.write('done.\n')
        # Clean up - no longer needed
        # os.unlink(distpath)

    def install_codev(self, context):
        self.install_via_pip(context, 'codev==%s' % self.version)

    # def install_setuptools(self, context):
    #     """
    #     Install setuptools in the environment.
    #
    #     :param context: The information for the environment creation request
    #                     being processed.
    #     """
    #     url = 'https://bitbucket.org/pypa/setuptools/downloads/ez_setup.py'
    #     self.install_script(context, 'setuptools', url)
    #     # clear up the setuptools archive which gets downloaded
    #     pred = lambda o: o.startswith('setuptools-') and o.endswith('.tar.gz')
    #     files = filter(pred, os.listdir(context.bin_path))
    #     for f in files:
    #         f = os.path.join(context.bin_path, f)
    #         os.unlink(f)
    #
    # def install_pip(self, context):
    #     """
    #     Install pip in the environment.
    #
    #     :param context: The information for the environment creation request
    #                     being processed.
    #     """
    #     url = 'https://raw.github.com/pypa/pip/master/contrib/get-pip.py'
    #     self.install_script(context, 'pip', url)


def create_codevenv(version):
    env_builder = CodevEnvBuilder(version, with_pip=True)
    env_builder.create(dir)
