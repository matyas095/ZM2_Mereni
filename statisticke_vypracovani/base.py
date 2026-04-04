from abc import ABC, abstractmethod;

class Method(ABC):
    name: str;
    description: str;

    @abstractmethod
    def get_args_info(self) -> list:
        ...

    @abstractmethod
    def run(self, args):
        ...

    def validate(self, args) -> None:
        pass;
