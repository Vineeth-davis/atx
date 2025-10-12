"""
Database Adapter Framework - Core Interface

This module defines the abstract base class and data structures for universal
database connectivity across different database engines.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    SQLSERVER = "sqlserver"
    MYSQL = "mysql"
    ORACLE = "oracle"
    MONGODB = "mongodb"
    SQLITE = "sqlite"


@dataclass
class ConnectionConfig:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_mode: Optional[str] = None
    connection_timeout: int = 30
    pool_size: int = 10
    max_overflow: int = 20
    driver: Optional[str] = None  # For SQL Server ODBC driver
    charset: Optional[str] = None  # For MySQL charset
    service_name: Optional[str] = None  # For Oracle service name


@dataclass
class QueryResult:
    """Result of a database query execution"""
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time: float
    query_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ColumnInfo:
    """Information about a database column"""
    name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str] = None
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_unique: bool = False
    is_indexed: bool = False
    description: Optional[str] = None


@dataclass
class ForeignKeyInfo:
    """Information about a foreign key constraint"""
    column_name: str
    referenced_table: str
    referenced_column: str
    constraint_name: str
    on_delete: Optional[str] = None
    on_update: Optional[str] = None


@dataclass
class IndexInfo:
    """Information about a database index"""
    name: str
    columns: List[str]
    is_unique: bool = False
    is_primary: bool = False
    is_clustered: bool = False
    fill_factor: Optional[int] = None
    description: Optional[str] = None


@dataclass
class TableInfo:
    """Information about a database table"""
    name: str
    schema: str
    columns: List[ColumnInfo]
    primary_keys: List[str]
    foreign_keys: List[ForeignKeyInfo]
    indexes: List[IndexInfo]
    row_count: int
    size_bytes: int
    description: Optional[str] = None
    business_domain: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class DatabaseSchema:
    """Complete database schema information"""
    database_name: str
    tables: List[TableInfo]
    views: List[TableInfo]
    functions: List[str]
    procedures: List[str]
    total_size_bytes: int
    version: Optional[str] = None
    charset: Optional[str] = None
    collation: Optional[str] = None
    description: Optional[str] = None


@dataclass
class QueryPlan:
    """Query execution plan information"""
    plan_type: str
    cost: Optional[float] = None
    rows_estimated: Optional[int] = None
    rows_actual: Optional[int] = None
    execution_time: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


class DatabaseAdapter(ABC):
    """
    Abstract base class for database adapters.
    
    This class defines the interface that all database adapters must implement
    to provide universal database connectivity across different database engines.
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize the database adapter.
        
        Args:
            config: Database connection configuration
        """
        self.config = config
        self.connection = None
        self.pool = None
        self.is_connected = False
        self._version = None
        self._schema_cache = None
        self._last_schema_refresh = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Close database connection.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> QueryResult:
        """
        Execute SQL query and return results.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            QueryResult: Query execution results
        """
        pass
    
    @abstractmethod
    async def execute_batch(self, queries: List[str]) -> List[QueryResult]:
        """
        Execute multiple queries in batch.
        
        Args:
            queries: List of SQL query strings
            
        Returns:
            List[QueryResult]: Results for each query
        """
        pass
    
    @abstractmethod
    async def get_schema(self, force_refresh: bool = False) -> DatabaseSchema:
        """
        Get complete database schema.
        
        Args:
            force_refresh: Force refresh of cached schema
            
        Returns:
            DatabaseSchema: Complete database schema information
        """
        pass
    
    @abstractmethod
    async def get_table_info(self, table_name: str, schema: Optional[str] = None) -> TableInfo:
        """
        Get detailed information about a specific table.
        
        Args:
            table_name: Name of the table
            schema: Optional schema name (defaults to default schema)
            
        Returns:
            TableInfo: Detailed table information
        """
        pass
    
    @abstractmethod
    async def get_table_data(self, table_name: str, limit: int = 100, offset: int = 0, 
                           schema: Optional[str] = None) -> QueryResult:
        """
        Get sample data from a table.
        
        Args:
            table_name: Name of the table
            limit: Maximum number of rows to return
            offset: Number of rows to skip
            schema: Optional schema name
            
        Returns:
            QueryResult: Sample data from the table
        """
        pass
    
    @abstractmethod
    async def validate_query(self, query: str) -> bool:
        """
        Validate SQL query syntax.
        
        Args:
            query: SQL query string to validate
            
        Returns:
            bool: True if query is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_query_plan(self, query: str) -> QueryPlan:
        """
        Get query execution plan.
        
        Args:
            query: SQL query string
            
        Returns:
            QueryPlan: Query execution plan information
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test database connectivity.
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def database_type(self) -> DatabaseType:
        """
        Return database type.
        
        Returns:
            DatabaseType: Type of database this adapter handles
        """
        pass
    
    @property
    async def version(self) -> str:
        """
        Return database version.
        
        Returns:
            str: Database version string
        """
        if self._version is None:
            try:
                self._version = await self._get_version()
            except Exception as e:
                logger.error(f"Failed to get database version: {e}")
                self._version = "Unknown"
        return self._version
    
    @abstractmethod
    async def _get_version(self) -> str:
        """
        Internal method to get database version.
        
        Returns:
            str: Database version string
        """
        pass
    
    async def get_table_names(self, schema: Optional[str] = None) -> List[str]:
        """
        Get list of table names in the database.
        
        Args:
            schema: Optional schema name
            
        Returns:
            List[str]: List of table names
        """
        schema_info = await self.get_schema()
        if schema:
            return [table.name for table in schema_info.tables if table.schema == schema]
        return [table.name for table in schema_info.tables]
    
    async def get_column_names(self, table_name: str, schema: Optional[str] = None) -> List[str]:
        """
        Get list of column names for a specific table.
        
        Args:
            table_name: Name of the table
            schema: Optional schema name
            
        Returns:
            List[str]: List of column names
        """
        table_info = await self.get_table_info(table_name, schema)
        return [column.name for column in table_info.columns]
    
    async def get_table_size(self, table_name: str, schema: Optional[str] = None) -> int:
        """
        Get the size of a table in bytes.
        
        Args:
            table_name: Name of the table
            schema: Optional schema name
            
        Returns:
            int: Table size in bytes
        """
        table_info = await self.get_table_info(table_name, schema)
        return table_info.size_bytes
    
    async def get_table_row_count(self, table_name: str, schema: Optional[str] = None) -> int:
        """
        Get the number of rows in a table.
        
        Args:
            table_name: Name of the table
            schema: Optional schema name
            
        Returns:
            int: Number of rows in the table
        """
        table_info = await self.get_table_info(table_name, schema)
        return table_info.row_count
    
    def _generate_query_id(self) -> str:
        """
        Generate a unique query ID.
        
        Returns:
            str: Unique query identifier
        """
        timestamp = datetime.utcnow()
        return f"{self.database_type.value}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
    
    def _sanitize_query(self, query: str) -> str:
        """
        Sanitize SQL query for security.
        
        Args:
            query: Raw SQL query
            
        Returns:
            str: Sanitized SQL query
        """
        # Basic sanitization - remove comments and normalize whitespace
        import re
        
        # Remove SQL comments
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


class DatabaseAdapterError(Exception):
    """Base exception for database adapter errors."""
    pass


class ConnectionError(DatabaseAdapterError):
    """Exception raised for connection-related errors."""
    pass


class QueryExecutionError(DatabaseAdapterError):
    """Exception raised for query execution errors."""
    pass


class SchemaError(DatabaseAdapterError):
    """Exception raised for schema-related errors."""
    pass


class ValidationError(DatabaseAdapterError):
    """Exception raised for validation errors."""
    pass
