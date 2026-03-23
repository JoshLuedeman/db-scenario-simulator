import threading
import pymssql
import psycopg2


class ConnectionManager:
    """Manages database connection configuration and creates new connections on demand."""

    def __init__(self):
        self.db_type = None
        self.config = {}
        self._lock = threading.Lock()

    @property
    def is_configured(self):
        return self.db_type is not None

    def configure(self, db_type, host, port, database, username, password):
        with self._lock:
            self.db_type = db_type
            self.config = {
                "host": host,
                "port": int(port),
                "database": database,
                "username": username,
                "password": password,
            }

    def disconnect(self):
        with self._lock:
            self.db_type = None
            self.config = {}

    def get_connection(self, autocommit=False):
        if not self.is_configured:
            raise RuntimeError("Not connected to a database")

        if self.db_type == "sqlserver":
            return pymssql.connect(
                server=self.config["host"],
                port=self.config["port"],
                user=self.config["username"],
                password=self.config["password"],
                database=self.config["database"],
                autocommit=autocommit,
            )
        elif self.db_type == "postgres":
            conn = psycopg2.connect(
                host=self.config["host"],
                port=self.config["port"],
                user=self.config["username"],
                password=self.config["password"],
                dbname=self.config["database"],
            )
            if autocommit:
                conn.autocommit = True
            return conn
        else:
            raise ValueError(f"Unknown db_type: {self.db_type}")

    def test_connection(self):
        conn = self.get_connection(autocommit=True)
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
        finally:
            conn.close()
        return True

    def get_info(self):
        if not self.is_configured:
            return None
        return {
            "db_type": self.db_type,
            "host": self.config["host"],
            "port": self.config["port"],
            "database": self.config["database"],
            "username": self.config["username"],
        }


conn_manager = ConnectionManager()
