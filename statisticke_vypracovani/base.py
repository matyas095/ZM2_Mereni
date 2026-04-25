from abc import ABC, abstractmethod;
from typing import Any;

class Method(ABC):
    """Bázová třída pro všechny statistické metody.

    Kontrakt:
        get_args_info() — definice CLI argumentů
        validate(args)  — validace vstupů, raise ValueError při chybě
        compute(args)   — čistý výpočet bez I/O (volitelné — pro programatické použití)
        run(args, do_print) — CLI entry point, volá validate → compute → print
    """
    name: str;
    description: str;

    @abstractmethod
    def get_args_info(self) -> list:
        ...

    @abstractmethod
    def run(self, args: Any, do_print: bool = True) -> dict:
        ...

    def validate(self, args: Any) -> None:
        """Validace vstupů. Výchozí implementace nic nedělá.

        Přetiž v podtřídě pro konkrétní kontroly.
        """


    def compute(self, args: Any) -> dict:
        """Čistý výpočet bez I/O — výchozí volá run(..., do_print=False).

        Přetiž v podtřídě pro čistší oddělení.
        """
        return self.run(args, do_print=False);
