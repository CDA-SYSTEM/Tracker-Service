from dataclasses import dataclass


@dataclass(frozen=True)
class Vehiculo:
    placa: str
    marca: str
    cliente_id: str
