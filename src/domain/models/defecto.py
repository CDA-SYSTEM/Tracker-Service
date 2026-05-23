from dataclasses import dataclass


@dataclass(frozen=True)
class Defecto:
    codigo_ntc5375: str
    descripcion: str = ""
