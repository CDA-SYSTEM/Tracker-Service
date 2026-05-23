from abc import ABC, abstractmethod

from src.domain.models.cliente import Cliente
from src.domain.models.defecto import Defecto
from src.domain.models.planilla import Planilla
from src.domain.models.vehiculo import Vehiculo


class ClienteRepository(ABC):

    @abstractmethod
    def crear(self, cliente: Cliente) -> None:
        ...

    @abstractmethod
    def obtener_por_id(self, cliente_id: str) -> Cliente | None:
        ...

    @abstractmethod
    def listar(self) -> list[Cliente]:
        ...

    @abstractmethod
    def contar_vehiculos(self, cliente_id: str) -> int:
        ...


class VehiculoRepository(ABC):

    @abstractmethod
    def crear(self, vehiculo: Vehiculo) -> None:
        ...

    @abstractmethod
    def asociar_a_cliente(self, cliente_id: str, placa: str) -> None:
        ...

    @abstractmethod
    def obtener_por_placa(self, placa: str) -> Vehiculo | None:
        ...

    @abstractmethod
    def listar(self) -> list[Vehiculo]:
        ...

    @abstractmethod
    def obtener_por_cliente(self, cliente_id: str) -> list[Vehiculo]:
        ...


class PlanillaRepository(ABC):

    @abstractmethod
    def crear(self, planilla: Planilla) -> None:
        ...

    @abstractmethod
    def agregar_defecto(self, planilla_id: str, codigo_ntc5375: str) -> None:
        ...

    @abstractmethod
    def obtener_por_id(self, planilla_id: str) -> Planilla | None:
        ...

    @abstractmethod
    def listar(self) -> list[Planilla]:
        ...

    @abstractmethod
    def obtener_por_vehiculo(self, placa: str) -> list[Planilla]:
        ...

    @abstractmethod
    def obtener_defectos(self, planilla_id: str) -> list[Defecto]:
        ...
