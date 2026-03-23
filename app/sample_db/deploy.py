import random
import math


def deploy_sample_db(conn_manager):
    if conn_manager.db_type == "sqlserver":
        _deploy_sqlserver(conn_manager)
    elif conn_manager.db_type == "postgres":
        _deploy_postgres(conn_manager)
    else:
        raise ValueError(f"Unsupported db_type: {conn_manager.db_type}")


def _deploy_sqlserver(conn_manager):
    conn = conn_manager.get_connection(autocommit=True)
    cur = conn.cursor()

    try:
        # Drop existing tables
        for table in [
            "scenario_events",
            "scenario_metrics",
            "scenario_orders",
            "scenario_inventory",
            "scenario_accounts",
        ]:
            cur.execute(
                f"IF OBJECT_ID('{table}', 'U') IS NOT NULL DROP TABLE {table}"
            )

        # Create tables
        cur.execute("""
            CREATE TABLE scenario_accounts (
                id INT PRIMARY KEY,
                account_name NVARCHAR(100),
                balance DECIMAL(18,2),
                status NVARCHAR(20),
                updated_at DATETIME2 DEFAULT GETDATE()
            )
        """)

        cur.execute("""
            CREATE TABLE scenario_inventory (
                id INT PRIMARY KEY,
                product_name NVARCHAR(100),
                quantity INT,
                warehouse NVARCHAR(50),
                updated_at DATETIME2 DEFAULT GETDATE()
            )
        """)

        cur.execute("""
            CREATE TABLE scenario_events (
                id INT IDENTITY(1,1) PRIMARY KEY,
                event_type NVARCHAR(50),
                payload NVARCHAR(MAX),
                created_at DATETIME2 DEFAULT GETDATE()
            )
        """)

        cur.execute("""
            CREATE TABLE scenario_orders (
                id INT IDENTITY(1,1) PRIMARY KEY,
                customer_id INT,
                order_date DATE,
                amount DECIMAL(18,2),
                status NVARCHAR(20),
                notes NVARCHAR(500)
            )
        """)

        cur.execute("""
            CREATE TABLE scenario_metrics (
                id INT IDENTITY(1,1) PRIMARY KEY,
                metric_name NVARCHAR(100),
                metric_value FLOAT,
                dimensions NVARCHAR(MAX),
                recorded_at DATETIME2 DEFAULT GETDATE()
            )
        """)

        # Seed accounts
        for i in range(1, 6):
            cur.execute(
                "INSERT INTO scenario_accounts (id, account_name, balance, status) "
                "VALUES (%s, %s, %s, %s)",
                (i, f"Account {chr(64 + i)}", i * 5000.0, "active"),
            )

        # Seed inventory
        products = [
            ("Widget Alpha", 500, "Warehouse-1"),
            ("Widget Beta", 300, "Warehouse-1"),
            ("Widget Gamma", 1000, "Warehouse-2"),
            ("Widget Delta", 200, "Warehouse-2"),
            ("Widget Epsilon", 750, "Warehouse-3"),
        ]
        for i, (name, qty, wh) in enumerate(products, 1):
            cur.execute(
                "INSERT INTO scenario_inventory (id, product_name, quantity, warehouse) "
                "VALUES (%s, %s, %s, %s)",
                (i, name, qty, wh),
            )

        # Seed orders (10,000 rows)
        statuses = ["completed", "pending", "shipped"]
        for i in range(1, 10001):
            cur.execute(
                "INSERT INTO scenario_orders (customer_id, order_date, amount, status, notes) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    i % 100 + 1,
                    f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                    round(math.fmod(i * 17.31, 999) + 1, 2),
                    statuses[i % 3],
                    f"Order notes for item {i}",
                ),
            )

        # Seed metrics (5,000 rows)
        regions = ["east", "west", "central"]
        for i in range(1, 5001):
            cur.execute(
                "INSERT INTO scenario_metrics (metric_name, metric_value, dimensions) "
                "VALUES (%s, %s, %s)",
                (
                    f"metric_{i % 10}",
                    round(random.random() * 100, 2),
                    f'{{"region":"{regions[i % 3]}"}}',
                ),
            )

        # Create indexes on orders
        cur.execute(
            "CREATE INDEX ix_orders_customer ON scenario_orders(customer_id)"
        )
        cur.execute(
            "CREATE INDEX ix_orders_date ON scenario_orders(order_date)"
        )
        cur.execute(
            "CREATE INDEX ix_orders_amount ON scenario_orders(amount)"
        )

    finally:
        conn.close()


def _deploy_postgres(conn_manager):
    conn = conn_manager.get_connection(autocommit=True)
    cur = conn.cursor()

    try:
        # Drop existing tables
        for table in [
            "scenario_events",
            "scenario_metrics",
            "scenario_orders",
            "scenario_inventory",
            "scenario_accounts",
        ]:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

        # Create tables
        cur.execute("""
            CREATE TABLE scenario_accounts (
                id INT PRIMARY KEY,
                account_name VARCHAR(100),
                balance DECIMAL(18,2),
                status VARCHAR(20),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE scenario_inventory (
                id INT PRIMARY KEY,
                product_name VARCHAR(100),
                quantity INT,
                warehouse VARCHAR(50),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE scenario_events (
                id SERIAL PRIMARY KEY,
                event_type VARCHAR(50),
                payload TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE scenario_orders (
                id SERIAL PRIMARY KEY,
                customer_id INT,
                order_date DATE,
                amount DECIMAL(18,2),
                status VARCHAR(20),
                notes VARCHAR(500)
            )
        """)

        cur.execute("""
            CREATE TABLE scenario_metrics (
                id SERIAL PRIMARY KEY,
                metric_name VARCHAR(100),
                metric_value DOUBLE PRECISION,
                dimensions JSONB,
                recorded_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Seed accounts
        for i in range(1, 6):
            cur.execute(
                "INSERT INTO scenario_accounts (id, account_name, balance, status) "
                "VALUES (%s, %s, %s, %s)",
                (i, f"Account {chr(64 + i)}", i * 5000.0, "active"),
            )

        # Seed inventory
        products = [
            ("Widget Alpha", 500, "Warehouse-1"),
            ("Widget Beta", 300, "Warehouse-1"),
            ("Widget Gamma", 1000, "Warehouse-2"),
            ("Widget Delta", 200, "Warehouse-2"),
            ("Widget Epsilon", 750, "Warehouse-3"),
        ]
        for i, (name, qty, wh) in enumerate(products, 1):
            cur.execute(
                "INSERT INTO scenario_inventory (id, product_name, quantity, warehouse) "
                "VALUES (%s, %s, %s, %s)",
                (i, name, qty, wh),
            )

        # Seed orders (10,000 rows)
        statuses = ["completed", "pending", "shipped"]
        for i in range(1, 10001):
            cur.execute(
                "INSERT INTO scenario_orders (customer_id, order_date, amount, status, notes) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    i % 100 + 1,
                    f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                    round(math.fmod(i * 17.31, 999) + 1, 2),
                    statuses[i % 3],
                    f"Order notes for item {i}",
                ),
            )

        # Seed metrics (5,000 rows)
        regions = ["east", "west", "central"]
        for i in range(1, 5001):
            cur.execute(
                "INSERT INTO scenario_metrics (metric_name, metric_value, dimensions) "
                "VALUES (%s, %s, %s::jsonb)",
                (
                    f"metric_{i % 10}",
                    round(random.random() * 100, 2),
                    f'{{"region":"{regions[i % 3]}"}}',
                ),
            )

        # Create indexes on orders
        cur.execute(
            "CREATE INDEX ix_orders_customer ON scenario_orders(customer_id)"
        )
        cur.execute(
            "CREATE INDEX ix_orders_date ON scenario_orders(order_date)"
        )
        cur.execute(
            "CREATE INDEX ix_orders_amount ON scenario_orders(amount)"
        )

    finally:
        conn.close()
