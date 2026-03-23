"""SQL dialect adapter — maps logical operations to platform-specific SQL."""


DIALECTS = {
    "sqlserver": {
        "sleep_30s": "WAITFOR DELAY '00:00:30'",
        "cpu_cross_join": (
            "SELECT COUNT(*) "
            "FROM scenario_orders a CROSS JOIN scenario_orders b "
            "WHERE CHECKSUM(a.amount, b.amount) % 100 = 0"
        ),
        "random_order_update": (
            "UPDATE scenario_orders SET amount = amount + 0.01 "
            "WHERE id = (SELECT TOP 1 id FROM scenario_orders ORDER BY NEWID())"
        ),
        "now": "GETDATE()",
    },
    "postgres": {
        "sleep_30s": "SELECT pg_sleep(30)",
        "cpu_cross_join": (
            "SELECT COUNT(*) "
            "FROM scenario_orders a CROSS JOIN scenario_orders b "
            "WHERE md5(a.amount::text || b.amount::text) LIKE '00%%'"
        ),
        "random_order_update": (
            "UPDATE scenario_orders SET amount = amount + 0.01 "
            "WHERE id = (SELECT id FROM scenario_orders ORDER BY RANDOM() LIMIT 1)"
        ),
        "now": "NOW()",
    },
}


def sql(db_type, key):
    """Return a SQL fragment for the given db_type and logical key."""
    return DIALECTS[db_type][key]
