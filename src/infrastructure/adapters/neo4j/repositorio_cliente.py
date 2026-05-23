from neo4j import Driver

from src.domain.models.cliente import Cliente
from src.domain.ports.repositories import ClienteRepository


class Neo4jClienteRepository(ClienteRepository):

    def __init__(self, driver: Driver) -> None:
        self._driver = driver

    def crear(self, cliente: Cliente) -> None:
        query = """
            CREATE (c:Cliente {id: $id, nombres: $nombres, documento: $documento})
        """
        params = {
            "id": cliente.id,
            "nombres": cliente.nombres,
            "documento": cliente.documento,
        }
        with self._driver.session() as session:
            session.run(query, params)

    def obtener_por_id(self, cliente_id: str) -> Cliente | None:
        query = """
            MATCH (c:Cliente {id: $id})
            RETURN c.id AS id, c.nombres AS nombres, c.documento AS documento
        """
        params = {"id": cliente_id}
        with self._driver.session() as session:
            result = session.run(query, params).single()
        if result is None:
            return None
        return Cliente(
            id=result["id"],
            nombres=result["nombres"],
            documento=result["documento"],
        )

    def listar(self) -> list[Cliente]:
        query = """
            MATCH (c:Cliente)
            RETURN c.id AS id, c.nombres AS nombres, c.documento AS documento
            ORDER BY c.nombres
        """
        with self._driver.session() as session:
            results = session.run(query)
            return [
                Cliente(
                    id=record["id"],
                    nombres=record["nombres"],
                    documento=record["documento"],
                )
                for record in results
            ]

    def contar_vehiculos(self, cliente_id: str) -> int:
        query = """
            MATCH (c:Cliente {id: $id})-[:POSEE]->(v:Vehiculo)
            RETURN count(v) AS total
        """
        params = {"id": cliente_id}
        with self._driver.session() as session:
            result = session.run(query, params).single()
        return result["total"] if result else 0
