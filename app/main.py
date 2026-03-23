import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.connection import conn_manager
from app.scenarios import get_scenario, get_scenarios_for_db, ALL_SCENARIOS
from app.sample_db.deploy import deploy_sample_db


# ---------------------------------------------------------------------------
# Lifespan — stop all running scenarios on shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(application: FastAPI):
    yield
    for s in ALL_SCENARIOS.values():
        if s.status == "running":
            s.stop()


app = FastAPI(title="DB Scenario Simulator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class ConnectRequest(BaseModel):
    db_type: str  # "sqlserver" or "postgres"
    host: str
    port: int
    database: str
    username: str
    password: str


class MessageResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Connection endpoints
# ---------------------------------------------------------------------------
@app.post("/api/connect", response_model=MessageResponse)
def connect(req: ConnectRequest):
    if req.db_type not in ("sqlserver", "postgres"):
        raise HTTPException(400, "db_type must be 'sqlserver' or 'postgres'")
    conn_manager.configure(
        db_type=req.db_type,
        host=req.host,
        port=req.port,
        database=req.database,
        username=req.username,
        password=req.password,
    )
    try:
        conn_manager.test_connection()
    except Exception as e:
        conn_manager.disconnect()
        raise HTTPException(400, f"Connection failed: {e}")
    return {"message": "Connected successfully"}


@app.post("/api/disconnect", response_model=MessageResponse)
def disconnect():
    # Stop all running scenarios first
    for s in ALL_SCENARIOS.values():
        if s.status == "running":
            s.stop()
    conn_manager.disconnect()
    return {"message": "Disconnected"}


@app.get("/api/connection")
def connection_info():
    info = conn_manager.get_info()
    return {"connected": info is not None, **(info or {})}


# ---------------------------------------------------------------------------
# Sample database
# ---------------------------------------------------------------------------
@app.post("/api/deploy-sample-db", response_model=MessageResponse)
def deploy_sample():
    if not conn_manager.is_configured:
        raise HTTPException(400, "Not connected to a database")
    try:
        deploy_sample_db(conn_manager)
    except Exception as e:
        raise HTTPException(500, f"Deploy failed: {e}")
    return {"message": "Sample database deployed successfully"}


# ---------------------------------------------------------------------------
# Scenario endpoints
# ---------------------------------------------------------------------------
@app.get("/api/scenarios")
def list_scenarios():
    if not conn_manager.is_configured:
        return []
    return [s.to_dict() for s in get_scenarios_for_db(conn_manager.db_type)]


@app.post("/api/scenarios/{scenario_id}/start", response_model=MessageResponse)
def start_scenario(scenario_id: str):
    if not conn_manager.is_configured:
        raise HTTPException(400, "Not connected to a database")
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(404, "Scenario not found")
    if conn_manager.db_type not in scenario.db_types:
        raise HTTPException(400, "Scenario not compatible with current database type")
    if scenario.status == "running":
        raise HTTPException(409, "Scenario is already running")
    try:
        # Start in a background thread so the HTTP response returns immediately
        t = threading.Thread(target=scenario.start, args=(conn_manager,), daemon=True)
        t.start()
    except Exception as e:
        raise HTTPException(500, str(e))
    return {"message": f"Scenario '{scenario.name}' started"}


@app.post("/api/scenarios/{scenario_id}/stop", response_model=MessageResponse)
def stop_scenario(scenario_id: str):
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(404, "Scenario not found")
    scenario.stop()
    return {"message": f"Scenario '{scenario.name}' stopped"}


@app.post("/api/scenarios/stop-all", response_model=MessageResponse)
def stop_all_scenarios():
    stopped = []
    for s in ALL_SCENARIOS.values():
        if s.status == "running":
            s.stop()
            stopped.append(s.name)
    return {"message": f"Stopped {len(stopped)} scenario(s)"}


# ---------------------------------------------------------------------------
# Serve the frontend
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    return open("app/static/index.html").read()
