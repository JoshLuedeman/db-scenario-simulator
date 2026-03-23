"""PostgreSQL-only scenarios — features unique to the PostgreSQL engine."""

import time
from app.scenarios.base import BaseScenario


class TableBloat(BaseScenario):
    id = "pg_bloat"
    name = "Table Bloat Generator"
    description = (
        "Repeatedly updates rows to create dead tuples, generating table bloat. "
        "Demonstrates need for VACUUM and visible in pg_stat_user_tables."
    )
    category = "Maintenance"
    db_types = ["postgres"]

    def _run(self, conn_manager):
        def bloater(thread_id):
            conn = None
            try:
                conn = conn_manager.get_connection(autocommit=True)
                self._register_connection(conn)
                cur = conn.cursor()
                while not self._stop_event.is_set():
                    cur.execute(
                        "UPDATE scenario_accounts SET balance = balance + 0.01, "
                        "updated_at = NOW()"
                    )
                    time.sleep(0.05)
            except Exception:
                pass
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        for i in range(3):
            self._spawn_thread(bloater, (i,))


class ConnectionSaturation(BaseScenario):
    id = "pg_connections"
    name = "Connection Saturation"
    description = (
        "Opens many idle connections to demonstrate connection pool exhaustion "
        "and the impact on max_connections. Visible in pg_stat_activity."
    )
    category = "Resource Pressure"
    db_types = ["postgres"]

    def _run(self, conn_manager):
        def open_connections():
            connections = []
            try:
                for i in range(50):
                    if self._stop_event.is_set():
                        break
                    try:
                        conn = conn_manager.get_connection(autocommit=True)
                        connections.append(conn)
                        self._register_connection(conn)
                    except Exception:
                        break
                    time.sleep(0.1)
                while not self._stop_event.wait(1):
                    pass
            finally:
                for c in connections:
                    try:
                        c.close()
                    except Exception:
                        pass

        self._spawn_thread(open_connections)


class WalPressure(BaseScenario):
    id = "pg_wal_pressure"
    name = "WAL Generation Pressure"
    description = (
        "Generates heavy WAL traffic through rapid writes and updates, "
        "useful for demonstrating WAL archiving and replication lag."
    )
    category = "Resource Pressure"
    db_types = ["postgres"]

    def _run(self, conn_manager):
        def wal_writer(thread_id):
            conn = None
            try:
                conn = conn_manager.get_connection(autocommit=True)
                self._register_connection(conn)
                cur = conn.cursor()
                while not self._stop_event.is_set():
                    cur.execute(
                        "INSERT INTO scenario_events (event_type, payload) VALUES (%s, %s)",
                        ("wal_pressure", "W" * 1000),
                    )
                    cur.execute(
                        "UPDATE scenario_orders SET amount = amount + 0.01 "
                        "WHERE id = (SELECT id FROM scenario_orders ORDER BY RANDOM() LIMIT 1)"
                    )
            except Exception:
                pass
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        for i in range(4):
            self._spawn_thread(wal_writer, (i,))


class VacuumPressure(BaseScenario):
    id = "pg_vacuum_pressure"
    name = "Vacuum Pressure"
    description = (
        "Creates conditions that demand aggressive vacuuming: rapid updates "
        "generating dead tuples plus a long-running transaction preventing cleanup."
    )
    category = "Maintenance"
    db_types = ["postgres"]

    def _run(self, conn_manager):
        def xid_holder():
            conn = None
            try:
                conn = conn_manager.get_connection()
                self._register_connection(conn)
                cur = conn.cursor()
                cur.execute("SELECT txid_current()")
                while not self._stop_event.wait(1):
                    pass
            except Exception:
                pass
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        def tuple_killer(thread_id):
            conn = None
            try:
                conn = conn_manager.get_connection(autocommit=True)
                self._register_connection(conn)
                cur = conn.cursor()
                while not self._stop_event.is_set():
                    cur.execute(
                        "UPDATE scenario_orders SET amount = amount + 0.01 "
                        "WHERE id BETWEEN %s AND %s",
                        (thread_id * 2500 + 1, (thread_id + 1) * 2500),
                    )
                    time.sleep(0.1)
            except Exception:
                pass
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        self._spawn_thread(xid_holder)
        for i in range(4):
            self._spawn_thread(tuple_killer, (i,))