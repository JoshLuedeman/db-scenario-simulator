"""SQL Server-only scenarios — features unique to the SQL Server engine."""

import random
import time
from app.scenarios.base import BaseScenario


class LockEscalation(BaseScenario):
    id = "ss_lock_escalation"
    name = "Lock Escalation"
    description = (
        "Updates many individual rows to accumulate row-level locks, triggering "
        "SQL Server to escalate to a table-level lock (~5000 row locks threshold)."
    )
    category = "Blocking & Locking"
    db_types = ["sqlserver"]

    def _run(self, conn_manager):
        def escalator():
            while not self._stop_event.is_set():
                conn = None
                try:
                    conn = conn_manager.get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE scenario_orders SET amount = amount + 0.01"
                    )
                    conn.commit()
                except Exception:
                    pass
                finally:
                    if conn:
                        try:
                            conn.close()
                        except Exception:
                            pass
                time.sleep(0.5)

        self._spawn_thread(escalator)


class TempdbPressure(BaseScenario):
    id = "ss_tempdb_pressure"
    name = "TempDB Pressure"
    description = (
        "Creates heavy TempDB usage through temp tables, large sorts, "
        "and spill operations across multiple concurrent sessions."
    )
    category = "Resource Pressure"
    db_types = ["sqlserver"]

    def _run(self, conn_manager):
        def tempdb_user(thread_id):
            while not self._stop_event.is_set():
                conn = None
                try:
                    conn = conn_manager.get_connection(autocommit=True)
                    self._register_connection(conn)
                    cur = conn.cursor()
                    suffix = f"t{thread_id}_{random.randint(1000, 9999)}"
                    cur.execute(f"""
                        SELECT id, customer_id, amount, notes,
                               ROW_NUMBER() OVER (ORDER BY NEWID()) as rn
                        INTO #temp_{suffix}
                        FROM scenario_orders
                    """)
                    cur.execute(f"""
                        SELECT customer_id, SUM(amount) as total, COUNT(*) as cnt
                        FROM #temp_{suffix}
                        GROUP BY customer_id
                        ORDER BY SUM(amount) DESC
                    """)
                    cur.fetchall()
                    cur.execute(f"DROP TABLE #temp_{suffix}")
                except Exception:
                    pass
                finally:
                    if conn:
                        try:
                            conn.close()
                        except Exception:
                            pass
                time.sleep(0.2)

        for i in range(4):
            self._spawn_thread(tempdb_user, (i,))


class MemoryGrantPressure(BaseScenario):
    id = "ss_memory_pressure"
    name = "Memory Grant Pressure"
    description = (
        "Runs queries that request large memory grants for sorting and hashing, "
        "causing memory contention visible in sys.dm_exec_query_memory_grants."
    )
    category = "Resource Pressure"
    db_types = ["sqlserver"]

    def _run(self, conn_manager):
        def memory_hog(thread_id):
            while not self._stop_event.is_set():
                conn = None
                try:
                    conn = conn_manager.get_connection(autocommit=True)
                    self._register_connection(conn)
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT TOP 1 a.id, a.amount, b.metric_value
                        FROM scenario_orders a
                        CROSS JOIN scenario_metrics b
                        ORDER BY a.amount * b.metric_value DESC
                    """)
                    cur.fetchone()
                except Exception:
                    pass
                finally:
                    if conn:
                        try:
                            conn.close()
                        except Exception:
                            pass
                time.sleep(0.5)

        for i in range(4):
            self._spawn_thread(memory_hog, (i,))