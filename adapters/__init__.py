"""
Database Adapters Package

This package contains database adapters for universal database connectivity.
"""

from .database_adapter import (
    DatabaseAdapter,
    DatabaseType,
    ConnectionConfig,
    QueryResult,
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo,
    TableInfo,
    DatabaseSchema,
    QueryPlan,
    DatabaseAdapterError,
    ConnectionError,
    QueryExecutionError,
    SchemaError,
    ValidationError
)

__all__ = [
    'DatabaseAdapter',
    'DatabaseType',
    'ConnectionConfig',
    'QueryResult',
    'ColumnInfo',
    'ForeignKeyInfo',
    'IndexInfo',
    'TableInfo',
    'DatabaseSchema',
    'QueryPlan',
    'DatabaseAdapterError',
    'ConnectionError',
    'QueryExecutionError',
    'SchemaError',
    'ValidationError'
]
