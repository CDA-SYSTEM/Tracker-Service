from dataclasses import dataclass


@dataclass(frozen=True)
class Cliente:
    id: str
    nombres: str
    documento: str
