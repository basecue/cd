
from contextlib import contextmanager
from os import path
from json import dumps
from time import sleep

from codev.core.executor import BaseExecutor
from .provider import Provider, ConfigurableProvider
from .scripts import COMMON_SCRIPTS


COMMON_SCRIPTS_PREFIX = 'codev/'
COMMON_SCRIPTS_PATH = '{directory}/scripts'.format(directory=path.dirname(__file__))



# class ScriptExecutor(ProxyExecutor):
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
#         with self.executor.change_directory(directory):
#             yield






