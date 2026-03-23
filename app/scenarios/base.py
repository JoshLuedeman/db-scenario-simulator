import threading
from abc import ABC, abstractmethod


class BaseScenario(ABC):
    id: str
    name: str
    description: str
    category: str
    db_types: list

    def __init__(self):
        self._stop_event = threading.Event()
        self._threads = []
        self._connections = []
        self._status = "idle"
        self._error = None
        self._lock = threading.Lock()

    @property
    def status(self):
        return self._status

    @property
    def error(self):
        return self._error

    def start(self, conn_manager):
        with self._lock:
            if self._status == "running":
                raise RuntimeError("Scenario is already running")
            self._stop_event.clear()
            self._threads = []
            self._connections = []
            self._status = "running"
            self._error = None

        try:
            self._run(conn_manager)
        except Exception as e:
            self._status = "error"
            self._error = str(e)
            raise

    @abstractmethod
    def _run(self, conn_manager):
        """Implement scenario logic. Spawn threads with _spawn_thread()."""
        pass

    def stop(self):
        self._stop_event.set()
        # Close all connections to unblock waiting queries
        for conn in self._connections:
            try:
                conn.close()
            except Exception:
                pass
        for t in self._threads:
            t.join(timeout=15)
        self._threads = []
        self._connections = []
        self._status = "idle"
        self._error = None

    def _spawn_thread(self, target, args=()):
        t = threading.Thread(target=target, args=args, daemon=True)
        self._threads.append(t)
        t.start()
        return t

    def _register_connection(self, conn):
        self._connections.append(conn)
        return conn

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "db_types": self.db_types,
            "status": self._status,
            "error": self._error,
        }
