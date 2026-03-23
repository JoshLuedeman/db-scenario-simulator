#!/bin/bash
# ─────────────────────────────────────────────────────────────
# run.sh — Launch DB Scenario Simulator
# Works with Docker (docker/docker compose) or Apple Containers (container).
# ─────────────────────────────────────────────────────────────
set -euo pipefail

APP_IMAGE="db-scenario-simulator"
APP_NAME="simulator"
APP_PORT=8080
SS_NAME="sqlserver"
SS_IMAGE="mcr.microsoft.com/mssql/server:2022-latest"
SS_PORT=1433
PG_NAME="postgres"
PG_IMAGE="postgres:16"
PG_PORT=5432

# ── Detect container runtime ────────────────────────────────
RUNTIME=""
if command -v container &>/dev/null; then
    RUNTIME="apple"
elif command -v docker &>/dev/null; then
    RUNTIME="docker"
else
    echo "Error: No container runtime found."
    echo "Install Docker Desktop (https://docker.com/products/docker-desktop)"
    echo "or enable Apple Containers on macOS 26+."
    exit 1
fi

echo "Container runtime: $RUNTIME"

# ── Parse arguments ─────────────────────────────────────────
PROFILE="${1:-app}"   # app | sqlserver | postgres | full
ACTION="${2:-up}"     # up | down

usage() {
    echo "Usage: $0 [profile] [action]"
    echo ""
    echo "Profiles:"
    echo "  app        Simulator only (default)"
    echo "  sqlserver  Simulator + SQL Server"
    echo "  postgres   Simulator + PostgreSQL"
    echo "  full       Simulator + SQL Server + PostgreSQL"
    echo ""
    echo "Actions:"
    echo "  up         Build and start containers (default)"
    echo "  down       Stop and remove containers"
    exit 0
}

[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && usage

# ─────────────────────────────────────────────────────────────
# Docker runtime — delegate to docker compose
# ─────────────────────────────────────────────────────────────
docker_up() {
    local compose_args=()
    if [[ "$PROFILE" != "app" ]]; then
        compose_args+=(--profile "$PROFILE")
    fi
    docker compose "${compose_args[@]}" up --build "$@"
}

docker_down() {
    local compose_args=()
    if [[ "$PROFILE" != "app" ]]; then
        compose_args+=(--profile "$PROFILE")
    fi
    docker compose "${compose_args[@]}" down "$@"
}

# ─────────────────────────────────────────────────────────────
# Apple Containers runtime
# ─────────────────────────────────────────────────────────────
apple_build_app() {
    echo "Building $APP_IMAGE from Containerfile..."
    container build --tag "$APP_IMAGE" --file Containerfile .
}

apple_run() {
    local name="$1" image="$2" port="$3"
    shift 3
    echo "Starting $name ($image) on port $port..."
    container run --name "$name" --publish "$port:$port" "$@" "$image" &
}

apple_start_sqlserver() {
    apple_run "$SS_NAME" "$SS_IMAGE" "$SS_PORT" \
        --env ACCEPT_EULA=Y \
        --env "MSSQL_SA_PASSWORD=ScenarioSim!2024"
}

apple_start_postgres() {
    apple_run "$PG_NAME" "$PG_IMAGE" "$PG_PORT" \
        --env "POSTGRES_PASSWORD=ScenarioSim2024" \
        --env "POSTGRES_DB=scenariodb"
}

apple_start_app() {
    apple_run "$APP_NAME" "$APP_IMAGE" "$APP_PORT" \
        --env PYTHONUNBUFFERED=1
}

apple_stop() {
    local name="$1"
    echo "Stopping $name..."
    container stop "$name" 2>/dev/null || true
    container rm "$name" 2>/dev/null || true
}

apple_up() {
    apple_build_app

    case "$PROFILE" in
        sqlserver)
            apple_start_sqlserver
            apple_start_app
            ;;
        postgres)
            apple_start_postgres
            apple_start_app
            ;;
        full)
            apple_start_sqlserver
            apple_start_postgres
            apple_start_app
            ;;
        app)
            apple_start_app
            ;;
    esac

    echo ""
    echo "Simulator running at http://localhost:$APP_PORT"
    echo "Press Ctrl+C to stop."
    wait
}

apple_down() {
    case "$PROFILE" in
        sqlserver)
            apple_stop "$SS_NAME"
            apple_stop "$APP_NAME"
            ;;
        postgres)
            apple_stop "$PG_NAME"
            apple_stop "$APP_NAME"
            ;;
        full)
            apple_stop "$SS_NAME"
            apple_stop "$PG_NAME"
            apple_stop "$APP_NAME"
            ;;
        app)
            apple_stop "$APP_NAME"
            ;;
    esac
    echo "All containers stopped."
}

# ─────────────────────────────────────────────────────────────
# Dispatch
# ─────────────────────────────────────────────────────────────
case "$RUNTIME" in
    docker)
        case "$ACTION" in
            up)   docker_up ;;
            down) docker_down ;;
            *)    usage ;;
        esac
        ;;
    apple)
        case "$ACTION" in
            up)   apple_up ;;
            down) apple_down ;;
            *)    usage ;;
        esac
        ;;
esac
