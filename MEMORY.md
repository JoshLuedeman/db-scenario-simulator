# Project Memory

This file captures project learnings that persist across agent sessions.

## Project Overview

**DB Scenario Simulator** — A mobile-friendly web application for database presenters and engineers to interactively simulate database scenarios (blocking, locking, deadlocks, high throughput, resource pressure, maintenance concerns) against SQL Server and PostgreSQL in real-time.

## Tech Stack

- **Language**: Python 3.12
- **Framework**: FastAPI (async REST API)
- **Server**: Uvicorn (ASGI)
- **Database Drivers**: pymssql (SQL Server), psycopg2-binary (PostgreSQL)
- **Frontend**: Vanilla HTML/CSS/JavaScript (single-page app, dark theme, mobile-first)
- **Container**: OCI Containerfile (compatible with Docker and Apple Containers)
- **Orchestration**: docker-compose.yml with profiles (sqlserver, postgres, full)
- **Launcher**: run.sh (auto-detects Docker vs Apple Containers runtime)

## Architecture

- **app/main.py** — FastAPI app with 11 REST endpoints, CORS, static file serving
- **app/connection.py** — Thread-safe ConnectionManager for on-demand DB connections
- **app/sample_db/deploy.py** — Dialect-aware schema deployment and seed data (5 tables, 15K+ rows)
- **app/scenarios/base.py** — Abstract BaseScenario with thread lifecycle, connection cleanup, stop signaling
- **app/scenarios/dialect.py** — SQL dialect adapter mapping logical operations to platform-specific SQL
- **app/scenarios/shared.py** — 7 cross-platform scenarios (blocking, deadlocks, throughput, batch, CPU, long-running, log growth)
- **app/scenarios/sqlserver.py** — 3 SQL Server-only scenarios (lock escalation, tempdb pressure, memory grants)
- **app/scenarios/postgres.py** — 4 PostgreSQL-only scenarios (bloat, connection saturation, WAL pressure, vacuum pressure)
- **app/scenarios/json_scenario.py** — JSON-driven scenario loader for drop-in extensibility
- **app/scenarios/custom/** — Directory for user-defined JSON scenario files (auto-discovered on startup)
- **app/static/index.html** — Complete SPA frontend

## Key Design Decisions

- **Registry pattern** for scenario discovery (ALL_SCENARIOS dict in __init__.py)
- **Abstract Base Class** for extensible scenarios with managed threading
- **Dialect abstraction** to write cross-platform scenarios without SQL duplication
- **JSON extensibility** — drop a .json file in custom/ folder to add scenarios without Python code
- **No external JS dependencies** — fully self-contained frontend
- **Thread-based concurrency** for scenario execution (non-blocking HTTP responses)
- **Cooperative cancellation** via threading.Event for graceful scenario shutdown

## Databases Supported

- SQL Server 2022 (via pymssql, port 1433)
- PostgreSQL 16 (via psycopg2, port 5432)

## Scenario Count

- 15 built-in Python scenarios + any number of JSON custom scenarios
- 7 shared, 3 SQL Server-only, 4 PostgreSQL-only, 1 JSON example included
