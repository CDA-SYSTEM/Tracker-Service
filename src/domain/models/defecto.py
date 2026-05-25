from dataclasses import dataclass


@dataclass(frozen=True)
class Defecto:
    codigo_ntc5375: str
    defect_type: str = ""
    observacion: str = ""
    descripcion: str = ""
