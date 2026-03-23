"""JSON-driven scenarios — drop a .json file in custom/ to add a scenario."""

import json
import logging
import os
import time

from app.scenarios.base import BaseScenario

logger = logging.getLogger(__name__)

CUSTOM_DIR = os.path.join(os.path.dirname(__file__), "custom")

REQUIRED_FIELDS = {"id", "name", "description", "category", "db_types", "threads"}


class JsonScenario(BaseScenario):
    """A scenario whose behaviour is defined entirely by a JSON file."""

    def __init__(self, definition: dict, source_file: str = "<inline>"):
        super().__init__()
        self.id = definition["id"]
        self.name = definition["name"]
        self.description = definition["description"]
        self.category = definition["category"]
        self.db_types = definition["db_types"]
        self._thread_defs = definition["threads"]
        self._source_file = source_file

    def _run(self, conn_manager):
        db_type = conn_manager.db_type
        for thread_def in self._thread_defs:
            count = thread_def.get("count", 1)
            for i in range(count):
                self._spawn_thread(self._worker, (conn_manager, thread_def, db_type, i))

    def _worker(self, conn_manager, thread_def, db_type, index):
        autocommit = thread_def.get("autocommit", False)
        loop = thread_def.get("loop", True)
        delay = thread_def.get("delay_seconds", 0)
        initial_delay = thread_def.get("initial_delay_seconds", 0)
        steps = thread_def.get("steps", [])

        if initial_delay and not self._stop_event.wait(initial_delay):
            pass
        elif initial_delay:
            return

        try:
            conn = conn_manager.get_connection(autocommit=autocommit)
            self._register_connection(conn)
            cursor = conn.cursor()
        except Exception as e:
            logger.error("JSON scenario %s thread %d connect failed: %s", self.id, index, e)
            return

        try:
            first = True
            while first or loop:
                first = False
                for step in steps:
                    if self._stop_event.is_set():
                        return
                    self._execute_step(step, cursor, conn, db_type)
                if delay and not self._stop_event.is_set():
                    self._stop_event.wait(delay)
        except Exception as e:
            logger.error("JSON scenario %s thread %d error: %s", self.id, index, e)

    def _execute_step(self, step, cursor, conn, db_type):
        if "sql" in step:
            raw = step["sql"]
            if isinstance(raw, dict):
                statement = raw.get(db_type)
                if statement is None:
                    return  # no SQL for this dialect — skip
            else:
                statement = raw
            cursor.execute(statement)

        elif "sleep" in step:
            self._stop_event.wait(step["sleep"])

        elif "commit" in step:
            conn.commit()

        elif "rollback" in step:
            conn.rollback()


def _validate(definition: dict, filepath: str) -> list[str]:
    """Return a list of validation errors (empty = valid)."""
    errors = []
    missing = REQUIRED_FIELDS - set(definition.keys())
    if missing:
        errors.append(f"Missing fields: {', '.join(sorted(missing))}")
        return errors

    if not isinstance(definition["db_types"], list) or not definition["db_types"]:
        errors.append("db_types must be a non-empty list")

    for val in definition.get("db_types", []):
        if val not in ("sqlserver", "postgres"):
            errors.append(f"Unknown db_type: {val!r}")

    if not isinstance(definition["threads"], list) or not definition["threads"]:
        errors.append("threads must be a non-empty list")

    for i, td in enumerate(definition.get("threads", [])):
        if not isinstance(td.get("steps"), list) or not td["steps"]:
            errors.append(f"Thread {i}: steps must be a non-empty list")

    return errors


def load_custom_scenarios() -> list[JsonScenario]:
    """Scan the custom/ directory and return validated JsonScenario instances."""
    scenarios = []
    if not os.path.isdir(CUSTOM_DIR):
        return scenarios

    for filename in sorted(os.listdir(CUSTOM_DIR)):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(CUSTOM_DIR, filename)
        try:
            with open(filepath, "r") as f:
                definition = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Skipping %s: %s", filename, e)
            continue

        errors = _validate(definition, filepath)
        if errors:
            logger.warning("Skipping %s: %s", filename, "; ".join(errors))
            continue

        scenarios.append(JsonScenario(definition, source_file=filepath))
        logger.info("Loaded custom scenario %r from %s", definition["id"], filename)

    return scenarios
