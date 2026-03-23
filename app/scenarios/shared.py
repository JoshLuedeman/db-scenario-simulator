"""Shared scenarios that run identically on SQL Server and PostgreSQL."""

import time
from app.scenarios.base import BaseScenario
from app.scenarios.dialect import sql


class BlockingChain(BaseScenario):
    id = "blocking"
    name = "Blocking Chain"
    description = (
        "Creates a chain of blocked sessions. Session 1 holds a lock, "
        "Session 2 waits on Session 1 while holding its own lock, "
        "Session 3 waits on Session 2."
    )
    category = "Blocking & Locking"
    db_types = ["sqlserver", "postgres"]

    def _run(self, conn_manager):
        def holder():
            try:
                conn = conn_manager.get_connection()
                self._register_connection(conn)
                cur = conn.cursor()
                cur.execute(
                    "UPDATE scenario_accounts SET balance = balance + 1 WHERE id = 1"
                )
                while not self._stop_event.wait(1):
                    pass
            except Exception:
                pass

        def waiter_1():
            time.sleep(1)
            try:
                conn = conn_manager.get_connection()
                self._register_connection(conn)
                cur = conn.cursor()
                cur.execute(
                    "UPDATE scenario_accounts SET balance = balance + 1 WHERE id = 2"
                )
                cur.execute(
                    "UPDATE scenario_accounts SET balance = balance + 1 WHERE id = 1"
                )
            except Exception:
                pass

        def waiter_2():
            time.sleep(2)
            try:
                conn = conn_manager.get_connection()
                self._register_connection(conn)
                cur = conn.cursor()
                cur.execute(
                    "UPDATE scenario_accounts SET balance = balance + 1 WHERE id = 2"
                )
            except Exception:
                pass

        self._spawn_thread(holder)
        self._spawn_thread(waiter_1)
        self._spawn_thread(waiter_2)


class DeadlockGenerator(BaseScenario):
    id = "deadlock"
    name = "Deadlock Generator"
    description = (
        "Continuously generates deadlocks between two sessions that lock "
        "resources in opposite order. The database engine detects and "
        "resolves them automatically."
    )
    category = "Blocking & Locking"
    db_types = ["sqlserver", "postgres"]

    def _run(self, conn_manager):
        is_pg = conn_manager.db_type == "postgres"

        def session_a():
            while not self._stop_event.is_set():
                conn = None
                try:
                    conn = conn_manager.get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE scenario_accounts SET balance = balance + 1 WHERE id = 1"
                    )
                    time.sleep(0.5)
                    cur.execute(
                        "UPDATE scenario_inventory SET quantity = quantity + 1 WHERE id = 1"
                    )
                    conn.commit()
                except Exception:
                    if is_pg and conn:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                finally:
                    if conn:
                        try:
                            conn.close()
                        except Exception:
                            pass
                time.sleep(0.5)

        def session_b():
            while not self._stop_event.is_set():
                conn = None
                try:
                    conn = conn_manager.get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE scenario_inventory SET quantity = quantity + 1 WHERE id = 1"
                    )
                    time.sleep(0.5)
                    cur.execute(
                        "UPDATE scenario_accounts SET balance = balance + 1 WHERE id = 1"
                    )
                    conn.commit()
                except Exception:
                    if is_pg and conn:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                finally:
                    if conn:
                        try:
                            conn.close()
                        except Exception:
                            pass
                time.sleep(0.5)

        self._spawn_thread(session_a)
        self._spawn_thread(session_b)


class HighThroughputInserts(BaseScenario):
    id = "high_throughput"
    name = "High Throughput Inserts"
    description = (
        "Multiple concurrent threads performing rapid-fire INSERT operations "
        "to simulate high write throughput and log/WAL activity."
    )
    category = "Performance & Load"
    db_types = ["sqlserver", "postgres"]

    def _run(self, conn_manager):
        def writer(thread_id):
            conn = None
            try:
                conn = conn_manager.get_connection(autocommit=True)
                self._register_connection(conn)
                cur = conn.cursor()
                while not self._stop_event.is_set():
                    cur.execute(
                        "INSERT INTO scenario_events (event_type, payload) VALUES (%s, %s)",
                        (f"throughput_t{thread_id}", "X" * 200),
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
            self._spawn_thread(writer, (i,))


class LargeBatchOperations(BaseScenario):
    id = "large_batch"
    name = "Large Batch Operations"
    description = (
        "Runs large batch transactions with thousands of rows per commit, "
        "demonstrating transaction log/WAL impact and lock duration."
    )
    category = "Performance & Load"
    db_types = ["sqlserver", "postgres"]

    def _run(self, conn_manager):
        is_pg = conn_manager.db_type == "postgres"

        def bulk_writer():
            while not self._stop_event.is_set():
                conn = None
                try:
                    conn = conn_manager.get_connection()
                    cur = conn.cursor()
                    for i in range(10000):
                        if self._stop_event.is_set():
                            break
                        cur.execute(
                            "INSERT INTO scenario_events (event_type, payload) VALUES (%s, %s)",
                            ("bulk_insert", "Y" * 500),
                        )
                    conn.commit()
                except Exception:
                    if is_pg and conn:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                finally:
                    if conn:
                        try:
                            conn.close()
                        except Exception:
                            pass
                time.sleep(0.5)

        self._spawn_thread(bulk_writer)


class CpuPressure(BaseScenario):
    id = "cpu_pressure"
    name = "CPU Pressure"
    description = (
        "Runs CPU-intensive cross-join queries to generate high processor "
        "utilization across multiple concurrent sessions."
    )
    category = "Resource Pressure"
    db_types = ["sqlserver", "postgres"]

    def _run(self, conn_manager):
        query = sql(conn_manager.db_type, "cpu_cross_join")

        def cpu_burner(thread_id):
            while not self._stop_event.is_set():
                conn = None
                try:
                    conn = conn_manager.get_connection(autocommit=True)
                    self._register_connection(conn)
                    cur = conn.cursor()
                    cur.execute(query)
                    cur.fetchone()
                except Exception:
                    pass
                finally:
                    if conn:
                        try:
                            conn.close()
                        except Exception:
                            pass
                time.sleep(0.2)

        for i in range(3):
            self._spawn_thread(cpu_burner, (i,))


class LongRunningQueries(BaseScenario):
    id = "long_running"
    name = "Long Running Queries"
    description = (
        "Runs multiple long-duration queries that remain active for extended "
        "periods, useful for demonstrating monitoring and session management."
    )
    category = "Performance & Load"
    db_types = ["sqlserver", "postgres"]

    def _run(self, conn_manager):
        sleep_sql = sql(conn_manager.db_type, "sleep_30s")

        def runner(session_id):
            while not self._stop_event.is_set():
                conn = None
                try:
                    conn = conn_manager.get_connection(autocommit=True)
                    self._register_connection(conn)
                    cur = conn.cursor()
                    cur.execute(sleep_sql)
                except Exception:
                    pass
                finally:
                    if conn:
                        try:
                            conn.close()
                        except Exception:
                            pass

        for i in range(3):
            self._spawn_thread(runner, (i,))


class LogGrowthPressure(BaseScenario):
    id = "log_growth"
    name = "Transaction Log / WAL Growth"
    description = (
        "Opens a long-running transaction and continuously inserts data "
        "without committing, causing transaction log (SQL Server) or WAL "
        "(PostgreSQL) growth."
    )
    category = "Resource Pressure"
    db_types = ["sqlserver", "postgres"]

    def _run(self, conn_manager):
        def log_grower():
            conn = None
            try:
                conn = conn_manager.get_connection()
                self._register_connection(conn)
                cur = conn.cursor()
                while not self._stop_event.is_set():
                    cur.execute(
                        "INSERT INTO scenario_events (event_type, payload) VALUES (%s, %s)",
                        ("log_growth", "Z" * 1000),
                    )
                    time.sleep(0.01)
            except Exception:
                pass
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        self._spawn_thread(log_grower)
