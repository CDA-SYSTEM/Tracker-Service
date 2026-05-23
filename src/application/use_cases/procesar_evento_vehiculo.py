from typing import Any

from src.domain.models.vehiculo import Vehiculo
from src.domain.ports.repositories import ClienteRepository, VehiculoRepository


class ProcesarEventoVehiculoCreado:

    def __init__(
        self,
        cliente_repo: ClienteRepository,
        vehiculo_repo: VehiculoRepository,
    ) -> None:
        self._cliente_repo = cliente_repo
        self._vehiculo_repo = vehiculo_repo

    def ejecutar(self, datos: dict[str, Any]) -> None:
        cliente_id: str = datos["cliente_id"]
        placa: str = datos["placa"]
        marca: str = datos["marca"]

        cliente = self._cliente_repo.obtener_por_id(cliente_id)
        if cliente is None:
            msg = f"Cliente con id {cliente_id} no encontrado"
            raise ValueError(msg)

        vehiculo = Vehiculo(placa=placa, marca=marca, cliente_id=cliente_id)
        self._vehiculo_repo.crear(vehiculo)
        self._vehiculo_repo.asociar_a_cliente(cliente_id, placa)
