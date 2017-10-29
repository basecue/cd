from contextlib import contextmanager
from os import path
from json import dumps

from .provider import Provider, ConfigurableProvider
from .scripts import COMMON_SCRIPTS


COMMON_SCRIPTS_PREFIX = 'codev/'
COMMON_SCRIPTS_PATH = '{directory}/scripts'.format(directory=path.dirname(__file__))


class CommandError(Exception):
    def __init__(self, command, exit_code, error, output=None):
        self.command = command
        self.exit_code = exit_code
        self.error = error
        self.output = output

        super().__init__(
            "Command '{command}' failed with exit code '{exit_code}' with error:\n{error}".format(
                command=command, exit_code=exit_code, error=error
            )
        )


class HasPerformer(object):
    def __init__(self, *args, performer, **kwargs):
        self.performer = performer
        super().__init__(*args, **kwargs)


#
# class Executor(HasPerformer):
#     def __init__(self, *args, base_dir='', **kwargs):
#         self.base_dir = base_dir
#         self.working_dirs = []
#         self.output_logger = getLogger('command_output')
#         super().__init__(*args, **kwargs)
#
#     def _include_command(self, command):
#         return command.replace('\\', '\\\\').replace('$', '\$').replace('"', '\\"')
#
#     def _prepare_command(self, command):
#         working_dir = self.working_dir
#         if working_dir:
#             command = 'cd {working_dir} && {command}'.format(
#                 working_dir=working_dir,
#                 command=command
#             )
#
#         return 'bash -c "{command}"'.format(
#             command=self._include_command(command)
#         )
#
#     @property
#     def working_dir(self):
#         return path.join(self.base_dir, *self.working_dirs)
#
#     @contextmanager
#     def change_base_dir(self, directory):
#         old_base_dir = self.base_dir
#         self.base_dir = directory
#         try:
#             yield
#         except:
#             raise
#         finally:
#             self.base_dir = old_base_dir
#
#     @contextmanager
#     def change_directory(self, directory):
#         self.working_dirs.append(directory)
#         try:
#             yield
#         except:
#             raise
#         finally:
#             self.working_dirs.pop()
#
#     def check_execute(self, command):
#         try:
#             self.execute(command)
#             return True
#         except CommandError:
#             return False
#
#     def _sanitize_path(self, path):
#         if path.startswith('~/'):
#             path = '{base_dir}/{path}'.format(
#                 base_dir=self.base_dir,
#                 path=path[2:]
#             )
#
#         if not path.startswith('/'):
#             path = '{working_dir}/{path}'.format(
#                 working_dir=self.working_dir,
#                 path=path
#             )
#         return path
#
#     def execute(self, command, logger=None, writein=None):
#         final_command = self._prepare_command(command)
#         return self.performer.perform(final_command, logger=logger, writein=writein)
#
#     def execute_wrapper(self, wrapper_command, command, logger=None, writein=None):
#         final_command = wrapper_command.format(
#             command=self._prepare_command(command)
#         )
#         return self.performer.perform(final_command, logger=logger, writein=writein)


class Performer(Provider, ConfigurableProvider):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
        # TODO move to future authentication module
        # if not self.check_execute('ssh-add -L'):
        #     raise CommandError("No SSH identities found, use the 'ssh-add'.")

    def perform(self, command, logger=None, writein=None):
        raise NotImplementedError()

    def send_file(self, source, target):
        raise NotImplementedError()

    @contextmanager
    def get_fo(self, remote_path):
        yield NotImplementedError()


# class ScriptExecutor(ProxyPerformer):
#
#     def execute_script(self, script, arguments=None, logger=None):
#         if arguments is None:
#             arguments = {}
#
#         # common scripts
#         if not path.isfile(script): # custom scripts have higher priority
#             for common_script, script_path in COMMON_SCRIPTS.items():
#                 script_ident = '{prefix}{common_script}'.format(
#                     prefix=COMMON_SCRIPTS_PREFIX,
#                     common_script=common_script
#                 )
#
#                 if script.startswith(script_ident):
#                     script_replace = '{common_scripts_path}/{script_path}'.format(
#                         common_scripts_path=COMMON_SCRIPTS_PATH,
#                         script_path=script_path
#                     )
#                     script = script.replace(script_ident, script_replace, 1)
#                     break
#
#         return self.execute(script.format(**arguments), writein=dumps(arguments), logger=logger)
#
#     def execute_scripts(self, scripts, common_arguments=None, logger=None):
#         if common_arguments is None:
#             common_arguments = {}
#         for script, arguments in scripts.items():
#             arguments.update(common_arguments)
#             self.execute_script(script, arguments, logger=logger)
#
#     def execute_scripts_onerror(self, scripts, arguments, error, logger=None):
#         logger.error(error)
#         arguments.update(
#             dict(
#                 command=error.command,
#                 exit_code=error.exit_code,
#                 error=error.error
#             )
#         )
#         self.execute_scripts(scripts, arguments)
#
#     @contextmanager
#     def change_directory(self, directory):
#         with self.performer.change_directory(directory):
#             yield






"""
Output reader
"""
from multiprocessing.pool import ThreadPool


class OutputReader(object):
    thread_pool = ThreadPool(processes=2)

    def __init__(self, stdout, stderr, logger=None):
        self._stdout_output = []
        self._stderr_output = []

        self.terminated = False

        self._stdout_reader = self.thread_pool.apply_async(
            self._reader,
            args=(stdout,),
            kwds=dict(logger=logger)
        )

        self._stderr_reader = self.thread_pool.apply_async(
            self._reader,
            args=(stderr,)
        )

    def _reader(self, output, logger=None):
        output_lines = []
        while True:
            try:
                if self.terminated:
                    output.flush()

                lines = output.readlines()
            except ValueError:  # closed file
                break

            if not lines:
                if self.terminated:
                    break

                sleep(0.1)
                continue

            for line in lines:
                output_line = line.decode('utf-8').rstrip('\n')
                output_lines.append(output_line)
                if logger:
                    logger.debug(output_line)

        return '\n'.join(output_lines)

    def output(self):
        self.terminated = True
        return self._stdout_reader.get(), self._stderr_reader.get()



