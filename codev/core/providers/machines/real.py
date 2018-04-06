from codev.core.machines import Machine


class RealMachine(Machine):
    provider_name = 'real'
    # settings_class = RealMachineSettings

    def exists(self) -> bool:
        return True

    def is_started(self) -> bool:
        return True

    def start(self) -> None:
        pass

    def create(self) -> None:
        pass

    def destroy(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def install_packages(self, *packages: str) -> None:
        # TODO use ssh executor
        pass

    @property
    def ip(self) -> str:
        # TODO rename to host
        # TODO this is workaround
        return self.ident


