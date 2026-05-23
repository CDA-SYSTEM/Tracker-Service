# Tracker Service — Trazabilidad CDA

Microservicio de proyección de datos (CQRS) para el Centro de Diagnóstico Automotor.
Consume eventos asíncronos de RabbitMQ y construye un grafo relacional en Neo4j con Clientes, Vehículos y Planillas de inspección (NTC 5375).

## Arquitectura

```
Dominio puro (models + ports)
  └── Application (use_cases)
        └── Infrastructure (adapters)
              ├── neo4j/    ← repositorios con Cypher
              ├── rabbitmq/ ← consumidor de eventos
              └── http/     ← Flask endpoints de lectura + Swagger
```

## Requisitos

- Python 3.11+
- Neo4j 5.x (accesible desde la red)
- RabbitMQ 3.x (con exchange `cda.domain.events` tipo `topic`)

## Entorno virtual (recomendado)

Sí, es necesario usar un entorno virtual para aislar las dependencias del proyecto
del Python del sistema. Esto evita conflictos entre proyectos.

### Windows (PowerShell)

```powershell
# 1. Clonar el repositorio
git clone <repo-url> tracker-service
cd tracker-service

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar entorno virtual
.venv\Scripts\Activate.ps1

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar variables de entorno
cp .env.example .env
# Editar .env con las credenciales del entorno

# 6. Ejecutar el servicio
python run.py
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# editar .env
python run.py
```

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `RABBITMQ_URI` | — | URI completa `amqp://user:pass@host:port` (prioritaria) |
| `RABBITMQ_HOST` | `100.94.204.56` | Host RabbitMQ |
| `RABBITMQ_PORT` | `5672` | Puerto RabbitMQ |
| `RABBITMQ_USER` | `guest` | Usuario RabbitMQ |
| `RABBITMQ_PASSWORD` | `guest` | Contraseña RabbitMQ |
| `RABBITMQ_QUEUE` | `tracker_service.queue` | Cola para consumo de eventos |
| `NEO4J_URI` | `bolt://100.94.204.56:7687` | URI de Neo4j |
| `NEO4J_USER` | `neo4j` | Usuario Neo4j |
| `NEO4J_PASSWORD` | `password` | Contraseña Neo4j |
| `FLASK_HOST` | `0.0.0.0` | IP de bind del servidor HTTP |
| `FLASK_PORT` | `5000` | Puerto del servidor HTTP |
| `API_KEY` | _(vacío)_ | Si se define, protege `/api/*` con header `X-API-Key` |

## Eventos que consume

| Routing key | Acción en Neo4j |
|---|---|
| `cliente.registro.creado` | Crea nodo `:Cliente {id, nombres, documento}` |
| `vehiculo.registro.creado` | Crea nodo `:Vehiculo {placa, marca}` y relación `(:Cliente)-[:POSEE]->(:Vehiculo)` |
| `inspeccion.planilla.completada` | Crea nodo `:Planilla {id}`, relación `(:Vehiculo)-[:TIENE_INSPECCION]->(:Planilla)`, nodos `:Defecto {codigo_ntc5375}` con relación `(:Planilla)-[:PRESENTA_DEFECTO]->(:Defecto)` |

## Endpoints HTTP

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/clientes` | Lista todos los clientes |
| `GET` | `/api/clientes/<id>` | Cliente por ID |
| `GET` | `/api/clientes/<id>/vehiculos` | Vehículos de un cliente |
| `GET` | `/api/vehiculos` | Lista todos los vehículos |
| `GET` | `/api/vehiculos/<placa>` | Vehículo por placa |
| `GET` | `/api/vehiculos/<placa>/planillas` | Planillas de inspección de un vehículo |
| `GET` | `/api/planillas` | Lista todas las planillas |
| `GET` | `/api/planillas/<id>` | Planilla con defectos NTC 5375 |

### Autenticación

Si la variable `API_KEY` está definida en el entorno, todos los endpoints
`/api/*` requieren el header:

```
X-API-Key: <valor-de-api-key>
```

Si `API_KEY` está vacío, el middleware se desactiva y los endpoints
son públicos (útil para desarrollo local).

## Documentación Swagger

Una vez corriendo el servicio, abrir en el navegador:

```
http://localhost:5000/apidocs/
```

## Postman

La colección de Postman está en [`postman/Tracker Service.postman_collection.json`](postman/Tracker%20Service.postman_collection.json).
Importarla en Postman y configurar las variables:

- `base_url` → `http://localhost:5000`
- `x_api_key` → valor de `API_KEY` (vacío si no se usa)
