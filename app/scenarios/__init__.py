from app.scenarios.shared import (
    BlockingChain,
    CpuPressure,
    DeadlockGenerator,
    HighThroughputInserts,
    LargeBatchOperations,
    LogGrowthPressure,
    LongRunningQueries,
)
from app.scenarios.sqlserver import (
    LockEscalation,
    MemoryGrantPressure,
    TempdbPressure,
)
from app.scenarios.postgres import (
    ConnectionSaturation,
    TableBloat,
    VacuumPressure,
    WalPressure,
)
from app.scenarios.json_scenario import load_custom_scenarios

ALL_SCENARIOS = {}


def _register(cls):
    instance = cls()
    ALL_SCENARIOS[instance.id] = instance


# Shared (SQL Server + PostgreSQL)
_register(BlockingChain)
_register(DeadlockGenerator)
_register(HighThroughputInserts)
_register(LargeBatchOperations)
_register(CpuPressure)
_register(LongRunningQueries)
_register(LogGrowthPressure)

# SQL Server only
_register(LockEscalation)
_register(TempdbPressure)
_register(MemoryGrantPressure)

# PostgreSQL only
_register(TableBloat)
_register(ConnectionSaturation)
_register(WalPressure)
_register(VacuumPressure)

# Custom JSON scenarios
for _custom in load_custom_scenarios():
    ALL_SCENARIOS[_custom.id] = _custom


def get_scenarios_for_db(db_type):
    return [s for s in ALL_SCENARIOS.values() if db_type in s.db_types]


def get_scenario(scenario_id):
    return ALL_SCENARIOS.get(scenario_id)