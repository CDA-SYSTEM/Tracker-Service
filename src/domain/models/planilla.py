from dataclasses import dataclass, field
from src.domain.models.defecto import Defecto


@dataclass(frozen=True)
class Planilla:
    id: str
    vehiculo_placa: str
    fecha: str = ""
    defectos: tuple[Defecto, ...] = field(default_factory=tuple)
