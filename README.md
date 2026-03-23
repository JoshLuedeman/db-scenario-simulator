# DB Scenario Simulator

A mobile-friendly web application for data platform presenters to simulate database scenarios (blocking, locking, high throughput, large transactions, resource pressure, etc.) against SQL Server and PostgreSQL.

## Quick Start

The project includes a unified launcher that auto-detects your container runtime (Docker or Apple Containers):

```bash
# Simulator only
./run.sh

# Simulator + SQL Server
./run.sh sqlserver

# Simulator + PostgreSQL
./run.sh postgres

# Simulator + both databases
./run.sh full

# Stop everything
./run.sh full down
```

Then open **http://localhost:8080** in a browser.

### Docker (direct commands)

```bash
# Build and run standalone
docker build -f Containerfile -t db-scenario-simulator .
docker run -p 8080:8080 db-scenario-simulator

# Or use docker compose with profiles
docker compose --profile full up --build
```

### Apple Containers (macOS 26+)

```bash
container build --tag db-scenario-simulator --file Containerfile .
container run --name simulator --publish 8080:8080 db-scenario-simulator
```

Default credentials for the compose databases:

| Engine | Host | Port | Username | Password |
|---|---|---|---|---|
| SQL Server | `sqlserver` | 1433 | `sa` | `ScenarioSim!2024` |
| PostgreSQL | `postgres` | 5432 | `postgres` | `ScenarioSim2024` |

## How It Works

1. **Connect** — Enter your database connection details (SQL Server or PostgreSQL).
2. **Deploy Sample DB** — One click deploys the sample tables and seed data the scenarios need.
3. **Run Scenarios** — Tap a scenario's **Start** button. The scenario runs in background threads against your database until you press **Stop**.

The UI auto-refreshes scenario status every 3 seconds.

## Scenarios

### Shared (SQL Server + PostgreSQL)

| Scenario | Category | Description |
|---|---|---|
| Blocking Chain | Blocking & Locking | Chain of blocked sessions waiting on each other |
| Deadlock Generator | Blocking & Locking | Continuous deadlocks from opposite-order locking |
| High Throughput Inserts | Performance & Load | Rapid-fire concurrent INSERT operations |
| Large Batch Operations | Performance & Load | 10,000-row transactions per commit |
| CPU Pressure | Resource Pressure | CPU-intensive cross-join queries |
| Long Running Queries | Performance & Load | 30-second queries across multiple sessions |
| Transaction Log / WAL Growth | Resource Pressure | Uncommitted transaction with continuous inserts |

### SQL Server Only

| Scenario | Category | Description |
|---|---|---|
| Lock Escalation | Blocking & Locking | Triggers row-to-table lock escalation |
| TempDB Pressure | Resource Pressure | Heavy temp table and sort spill usage |
| Memory Grant Pressure | Resource Pressure | Large memory grant contention |

### PostgreSQL Only

| Scenario | Category | Description |
|---|---|---|
| Table Bloat Generator | Maintenance | Dead tuple accumulation for vacuum demos |
| Connection Saturation | Resource Pressure | Opens 50 idle connections |
| WAL Generation Pressure | Resource Pressure | Heavy WAL traffic from writes + updates |
| Vacuum Pressure | Maintenance | Long-running xact blocks vacuum cleanup |

## Project Structure

```
db-scenario-simulator/
├── Containerfile            # OCI container image (Docker + Apple Containers)
├── docker-compose.yml       # Docker Compose orchestration
├── run.sh                   # Unified launcher (auto-detects runtime)
├── requirements.txt
└── app/
    ├── main.py              # FastAPI application
    ├── connection.py         # Connection manager
    ├── static/
    │   └── index.html        # Mobile-friendly SPA
    ├── sample_db/
    │   └── deploy.py         # Sample table/data deployment
    └── scenarios/
        ├── __init__.py       # Registry + auto-discovery
        ├── base.py           # BaseScenario ABC
        ├── dialect.py        # SQL dialect adapter
        ├── json_scenario.py  # JSON scenario loader
        ├── shared.py         # Cross-platform scenarios
        ├── sqlserver.py      # SQL Server-only scenarios
        ├── postgres.py       # PostgreSQL-only scenarios
        └── custom/           # Drop .json files here to add scenarios
            └── *.json
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/connect` | Connect to a database |
| `POST` | `/api/disconnect` | Disconnect and stop all scenarios |
| `GET` | `/api/connection` | Current connection info |
| `POST` | `/api/deploy-sample-db` | Deploy sample tables and seed data |
| `GET` | `/api/scenarios` | List scenarios for current db type |
| `POST` | `/api/scenarios/{id}/start` | Start a scenario |
| `POST` | `/api/scenarios/{id}/stop` | Stop a scenario |
| `POST` | `/api/scenarios/stop-all` | Stop all running scenarios |
