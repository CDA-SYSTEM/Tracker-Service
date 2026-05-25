from neo4j import Driver

from src.domain.models.defecto import Defecto
from src.domain.models.planilla import Planilla
from src.domain.ports.repositories import PlanillaRepository


class Neo4jPlanillaRepository(PlanillaRepository):

    def __init__(self, driver: Driver) -> None:
        self._driver = driver

    def crear(self, planilla: Planilla) -> None:
        query = """
            MATCH (v:Vehiculo {placa: $placa})
            CREATE (p:Planilla {id: $id, fecha: $fecha})
            CREATE (v)-[:TIENE_INSPECCION]->(p)
            WITH p
            UNWIND $defectos AS d
            CREATE (def:Defecto {
                codigo_ntc5375: d.codigo,
                defect_type: d.tipo,
                observacion: d.obs
            })
            CREATE (p)-[:PRESENTA_DEFECTO]->(def)
        """
        params = {
            "id": planilla.id,
            "placa": planilla.vehiculo_placa,
            "fecha": planilla.fecha,
            "defectos": [
                {
                    "codigo": d.codigo_ntc5375,
                    "tipo": d.defect_type,
                    "obs": d.observacion,
                }
                for d in planilla.defectos
            ],
        }
        with self._driver.session() as session:
            session.run(query, params)

    def agregar_defecto(self, planilla_id: str, codigo_ntc5375: str) -> None:
        query = """
            MATCH (p:Planilla {id: $planilla_id})
            CREATE (d:Defecto {codigo_ntc5375: $codigo})
            CREATE (p)-[:PRESENTA_DEFECTO]->(d)
        """
        params = {
            "planilla_id": planilla_id,
            "codigo": codigo_ntc5375,
        }
        with self._driver.session() as session:
            session.run(query, params)

    def obtener_por_id(self, planilla_id: str) -> Planilla | None:
        query = """
            MATCH (p:Planilla {id: $id})
            OPTIONAL MATCH (v:Vehiculo)-[:TIENE_INSPECCION]->(p)
            RETURN p.id AS id,
                   v.placa AS vehiculo_placa,
                   p.fecha AS fecha
        """
        params = {"id": planilla_id}
        with self._driver.session() as session:
            result = session.run(query, params).single()
        if result is None:
            return None
        return Planilla(
            id=result["id"],
            vehiculo_placa=result["vehiculo_placa"] or "",
            fecha=result.get("fecha", "") or "",
        )

    def listar(self) -> list[Planilla]:
        query = """
            MATCH (p:Planilla)
            OPTIONAL MATCH (v:Vehiculo)-[:TIENE_INSPECCION]->(p)
            RETURN p.id AS id, v.placa AS vehiculo_placa, p.fecha AS fecha
            ORDER BY p.id
        """
        with self._driver.session() as session:
            results = session.run(query)
            return [
                Planilla(
                    id=record["id"],
                    vehiculo_placa=record["vehiculo_placa"] or "",
                    fecha=record.get("fecha", "") or "",
                )
                for record in results
            ]

    def obtener_por_vehiculo(self, placa: str) -> list[Planilla]:
        query = """
            MATCH (v:Vehiculo {placa: $placa})-[:TIENE_INSPECCION]->(p:Planilla)
            RETURN p.id AS id, v.placa AS vehiculo_placa, p.fecha AS fecha
            ORDER BY p.id
        """
        params = {"placa": placa}
        with self._driver.session() as session:
            results = session.run(query, params)
            return [
                Planilla(
                    id=record["id"],
                    vehiculo_placa=record["vehiculo_placa"],
                    fecha=record.get("fecha", "") or "",
                )
                for record in results
            ]

    def obtener_defectos(self, planilla_id: str) -> list[Defecto]:
        query = """
            MATCH (p:Planilla {id: $id})-[:PRESENTA_DEFECTO]->(d:Defecto)
            RETURN d.codigo_ntc5375 AS codigo_ntc5375,
                   d.defect_type AS defect_type,
                   d.observacion AS observacion
            ORDER BY d.codigo_ntc5375
        """
        params = {"id": planilla_id}
        with self._driver.session() as session:
            results = session.run(query, params)
            return [
                Defecto(
                    codigo_ntc5375=record["codigo_ntc5375"],
                    defect_type=record.get("defect_type", "") or "",
                    observacion=record.get("observacion", "") or "",
                )
                for record in results
            ]
