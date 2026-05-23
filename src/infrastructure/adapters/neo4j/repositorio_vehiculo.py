from neo4j import Driver

from src.domain.models.vehiculo import Vehiculo
from src.domain.ports.repositories import VehiculoRepository


class Neo4jVehiculoRepository(VehiculoRepository):

    def __init__(self, driver: Driver) -> None:
        self._driver = driver

    def crear(self, vehiculo: Vehiculo) -> None:
        query = """
            CREATE (v:Vehiculo {placa: $placa, marca: $marca})
        """
        params = {
            "placa": vehiculo.placa,
            "marca": vehiculo.marca,
        }
        with self._driver.session() as session:
            session.run(query, params)

    def asociar_a_cliente(self, cliente_id: str, placa: str) -> None:
        query = """
            MATCH (c:Cliente {id: $cliente_id})
            MATCH (v:Vehiculo {placa: $placa})
            CREATE (c)-[:POSEE]->(v)
        """
        params = {
            "cliente_id": cliente_id,
            "placa": placa,
        }
        with self._driver.session() as session:
            session.run(query, params)

    def obtener_por_placa(self, placa: str) -> Vehiculo | None:
        query = """
            MATCH (v:Vehiculo {placa: $placa})
            OPTIONAL MATCH (c:Cliente)-[:POSEE]->(v)
            RETURN v.placa AS placa,
                   v.marca AS marca,
                   c.id AS cliente_id
        """
        params = {"placa": placa}
        with self._driver.session() as session:
            result = session.run(query, params).single()
        if result is None:
            return None
        return Vehiculo(
            placa=result["placa"],
            marca=result["marca"],
            cliente_id=result["cliente_id"] or "",
        )

    def listar(self) -> list[Vehiculo]:
        query = """
            MATCH (v:Vehiculo)
            OPTIONAL MATCH (c:Cliente)-[:POSEE]->(v)
            RETURN v.placa AS placa,
                   v.marca AS marca,
                   c.id AS cliente_id
            ORDER BY v.placa
        """
        with self._driver.session() as session:
            results = session.run(query)
            return [
                Vehiculo(
                    placa=record["placa"],
                    marca=record["marca"],
                    cliente_id=record["cliente_id"] or "",
                )
                for record in results
            ]

    def obtener_por_cliente(self, cliente_id: str) -> list[Vehiculo]:
        query = """
            MATCH (c:Cliente {id: $cliente_id})-[:POSEE]->(v:Vehiculo)
            RETURN v.placa AS placa,
                   v.marca AS marca,
                   c.id AS cliente_id
            ORDER BY v.placa
        """
        params = {"cliente_id": cliente_id}
        with self._driver.session() as session:
            results = session.run(query, params)
            return [
                Vehiculo(
                    placa=record["placa"],
                    marca=record["marca"],
                    cliente_id=record["cliente_id"],
                )
                for record in results
            ]
