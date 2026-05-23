from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class EventConsumer(ABC):

    @abstractmethod
    def iniciar_consumo(
        self,
        routing_key: str,
        callback: Callable[[dict[str, Any]], None],
    ) -> None:
        ...

    @abstractmethod
    def detener(self) -> None:
        ...
