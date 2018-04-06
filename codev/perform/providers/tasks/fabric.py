from typing import Optional, Any, Dict

from codev.core import BaseSettings
from codev.core.providers import VirtualenvBaseMachine
from codev.core.settings import SettingsError
from codev.core.utils import Ident, Status

from codev.perform.infrastructure import Infrastructure
from codev.perform.task import Task


class FabricTaskSettings(BaseSettings):
    @property
    def role(self) -> Optional[str]:
        return self.data.get('role')

    @property
    def version(self) -> Optional[str]:
        return self.data.get('version')

    @property
    def task(self) -> str:
        try:
            return self.data['task']
        except KeyError:
            raise SettingsError('Task must be specified for Fabric task.')


class FabricTask(Task):
    provider_name = 'fabric'
    settings_class = FabricTaskSettings

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.isolator = VirtualenvBaseMachine(
            executor=self.executor,
            settings_data=dict(python='2'),
            ident=Ident('codevfabric')
        )

    def prepare(self) -> None:
        # TODO requirements - python-dev, python-virtualenv
        self.isolator.create()
        self.isolator.execute('pip install setuptools')

        version_add = ''
        if self.settings.version:
            version_add = '==%s' % self.settings.version
        self.isolator.execute('pip install --upgrade fabric%s fabtools' % version_add)

    def run(self, infrastructure: Infrastructure, status: Status, input_vars: Dict[str, str]) -> bool:
        self.isolator.execute('fab {task} -R {role}'.format(
            task=self.settings.task,
            role=self.settings.role
        ))

        return True
