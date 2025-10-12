"""
Unit tests for Database Adapter Framework

Tests the core database adapter interface and data structures.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Optional, Any

from adapters.database_adapter import (
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


class MockDatabaseAdapter(DatabaseAdapter):
    """Mock implementation of DatabaseAdapter for testing."""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self._mock_connected = False
        self._mock_version = "Mock DB 1.0.0"
        self._mock_schema = None
    
    @property
    def database_type(self) -> DatabaseType:
        return DatabaseType.POSTGRESQL
    
    async def connect(self) -> bool:
        self._mock_connected = True
        self.is_connected = True
        return True
    
    async def disconnect(self) -> bool:
        self._mock_connected = False
        self.is_connected = False
        return True
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> QueryResult:
        if not self._mock_connected:
            raise ConnectionError("Not connected to database")
        
        # Mock query execution
        mock_data = [{"id": 1, "name": "test"}, {"id": 2, "name": "test2"}]
        return QueryResult(
            data=mock_data,
            columns=["id", "name"],
            row_count=len(mock_data),
            execution_time=0.001,
            query_id=self._generate_query_id(),
            timestamp=datetime.utcnow(),
            metadata={"database": "mock"}
        )
    
    async def execute_batch(self, queries: List[str]) -> List[QueryResult]:
        results = []
        for query in queries:
            result = await self.execute_query(query)
            results.append(result)
        return results
    
    async def get_schema(self, force_refresh: bool = False) -> DatabaseSchema:
        if self._mock_schema is None or force_refresh:
            self._mock_schema = DatabaseSchema(
                database_name=self.config.database,
                tables=[
                    TableInfo(
                        name="test_table",
                        schema="public",
                        columns=[
                            ColumnInfo(name="id", data_type="integer", is_nullable=False, is_primary_key=True),
                            ColumnInfo(name="name", data_type="varchar", is_nullable=True)
                        ],
                        primary_keys=["id"],
                        foreign_keys=[],
                        indexes=[],
                        row_count=100,
                        size_bytes=8192
                    )
                ],
                views=[],
                functions=[],
                procedures=[],
                total_size_bytes=8192
            )
        return self._mock_schema
    
    async def get_table_info(self, table_name: str, schema: Optional[str] = None) -> TableInfo:
        schema_info = await self.get_schema()
        for table in schema_info.tables:
            if table.name == table_name and (schema is None or table.schema == schema):
                return table
        raise SchemaError(f"Table {table_name} not found")
    
    async def get_table_data(self, table_name: str, limit: int = 100, offset: int = 0, 
                           schema: Optional[str] = None) -> QueryResult:
        return await self.execute_query(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}")
    
    async def validate_query(self, query: str) -> bool:
        # Simple validation - check for basic SQL keywords
        query_lower = query.lower().strip()
        return query_lower.startswith(('select', 'insert', 'update', 'delete', 'create', 'drop', 'alter'))
    
    async def get_query_plan(self, query: str) -> QueryPlan:
        return QueryPlan(
            plan_type="mock_plan",
            cost=1.0,
            rows_estimated=100,
            execution_time=0.001,
            details={"type": "mock"}
        )
    
    async def test_connection(self) -> bool:
        return self._mock_connected
    
    async def _get_version(self) -> str:
        return self._mock_version


class TestDatabaseType:
    """Test DatabaseType enum."""
    
    def test_database_type_values(self):
        """Test that DatabaseType has expected values."""
        assert DatabaseType.POSTGRESQL.value == "postgresql"
        assert DatabaseType.SQLSERVER.value == "sqlserver"
        assert DatabaseType.MYSQL.value == "mysql"
        assert DatabaseType.ORACLE.value == "oracle"
        assert DatabaseType.MONGODB.value == "mongodb"
        assert DatabaseType.SQLITE.value == "sqlite"


class TestConnectionConfig:
    """Test ConnectionConfig dataclass."""
    
    def test_connection_config_creation(self):
        """Test creating a ConnectionConfig."""
        config = ConnectionConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_password"
        )
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "test_db"
        assert config.username == "test_user"
        assert config.password == "test_password"
        assert config.connection_timeout == 30
        assert config.pool_size == 10
        assert config.max_overflow == 20
    
    def test_connection_config_optional_fields(self):
        """Test ConnectionConfig with optional fields."""
        config = ConnectionConfig(
            host="localhost",
            port=1433,
            database="test_db",
            username="test_user",
            password="test_password",
            ssl_mode="require",
            connection_timeout=60,
            pool_size=20,
            driver="ODBC Driver 17 for SQL Server"
        )
        
        assert config.ssl_mode == "require"
        assert config.connection_timeout == 60
        assert config.pool_size == 20
        assert config.driver == "ODBC Driver 17 for SQL Server"


class TestQueryResult:
    """Test QueryResult dataclass."""
    
    def test_query_result_creation(self):
        """Test creating a QueryResult."""
        timestamp = datetime.utcnow()
        result = QueryResult(
            data=[{"id": 1, "name": "test"}],
            columns=["id", "name"],
            row_count=1,
            execution_time=0.001,
            query_id="test_query_123",
            timestamp=timestamp,
            metadata={"database": "test"}
        )
        
        assert result.data == [{"id": 1, "name": "test"}]
        assert result.columns == ["id", "name"]
        assert result.row_count == 1
        assert result.execution_time == 0.001
        assert result.query_id == "test_query_123"
        assert result.timestamp == timestamp
        assert result.metadata == {"database": "test"}
        assert result.error is None


class TestColumnInfo:
    """Test ColumnInfo dataclass."""
    
    def test_column_info_creation(self):
        """Test creating a ColumnInfo."""
        column = ColumnInfo(
            name="user_id",
            data_type="integer",
            is_nullable=False,
            default_value="0",
            max_length=None,
            precision=10,
            scale=0,
            is_primary_key=True,
            is_foreign_key=False,
            description="User identifier"
        )
        
        assert column.name == "user_id"
        assert column.data_type == "integer"
        assert column.is_nullable is False
        assert column.default_value == "0"
        assert column.precision == 10
        assert column.scale == 0
        assert column.is_primary_key is True
        assert column.is_foreign_key is False
        assert column.description == "User identifier"


class TestForeignKeyInfo:
    """Test ForeignKeyInfo dataclass."""
    
    def test_foreign_key_info_creation(self):
        """Test creating a ForeignKeyInfo."""
        fk = ForeignKeyInfo(
            column_name="user_id",
            referenced_table="users",
            referenced_column="id",
            constraint_name="fk_user_id",
            on_delete="CASCADE",
            on_update="RESTRICT"
        )
        
        assert fk.column_name == "user_id"
        assert fk.referenced_table == "users"
        assert fk.referenced_column == "id"
        assert fk.constraint_name == "fk_user_id"
        assert fk.on_delete == "CASCADE"
        assert fk.on_update == "RESTRICT"


class TestIndexInfo:
    """Test IndexInfo dataclass."""
    
    def test_index_info_creation(self):
        """Test creating an IndexInfo."""
        index = IndexInfo(
            name="idx_user_email",
            columns=["email"],
            is_unique=True,
            is_primary=False,
            is_clustered=False,
            fill_factor=90,
            description="Unique index on email"
        )
        
        assert index.name == "idx_user_email"
        assert index.columns == ["email"]
        assert index.is_unique is True
        assert index.is_primary is False
        assert index.is_clustered is False
        assert index.fill_factor == 90
        assert index.description == "Unique index on email"


class TestTableInfo:
    """Test TableInfo dataclass."""
    
    def test_table_info_creation(self):
        """Test creating a TableInfo."""
        columns = [
            ColumnInfo(name="id", data_type="integer", is_nullable=False, is_primary_key=True),
            ColumnInfo(name="name", data_type="varchar", is_nullable=True)
        ]
        
        table = TableInfo(
            name="users",
            schema="public",
            columns=columns,
            primary_keys=["id"],
            foreign_keys=[],
            indexes=[],
            row_count=1000,
            size_bytes=16384,
            description="User table",
            business_domain="crm"
        )
        
        assert table.name == "users"
        assert table.schema == "public"
        assert len(table.columns) == 2
        assert table.primary_keys == ["id"]
        assert table.row_count == 1000
        assert table.size_bytes == 16384
        assert table.description == "User table"
        assert table.business_domain == "crm"


class TestDatabaseSchema:
    """Test DatabaseSchema dataclass."""
    
    def test_database_schema_creation(self):
        """Test creating a DatabaseSchema."""
        tables = [
            TableInfo(
                name="users",
                schema="public",
                columns=[],
                primary_keys=[],
                foreign_keys=[],
                indexes=[],
                row_count=0,
                size_bytes=0
            )
        ]
        
        schema = DatabaseSchema(
            database_name="test_db",
            tables=tables,
            views=[],
            functions=["get_user_count"],
            procedures=["create_user"],
            total_size_bytes=16384,
            version="PostgreSQL 13.0",
            charset="UTF8",
            collation="en_US.UTF-8"
        )
        
        assert schema.database_name == "test_db"
        assert len(schema.tables) == 1
        assert schema.functions == ["get_user_count"]
        assert schema.procedures == ["create_user"]
        assert schema.total_size_bytes == 16384
        assert schema.version == "PostgreSQL 13.0"
        assert schema.charset == "UTF8"
        assert schema.collation == "en_US.UTF-8"


class TestQueryPlan:
    """Test QueryPlan dataclass."""
    
    def test_query_plan_creation(self):
        """Test creating a QueryPlan."""
        plan = QueryPlan(
            plan_type="Seq Scan",
            cost=10.0,
            rows_estimated=1000,
            rows_actual=950,
            execution_time=0.05,
            details={"table": "users", "filter": "active = true"}
        )
        
        assert plan.plan_type == "Seq Scan"
        assert plan.cost == 10.0
        assert plan.rows_estimated == 1000
        assert plan.rows_actual == 950
        assert plan.execution_time == 0.05
        assert plan.details == {"table": "users", "filter": "active = true"}


class TestDatabaseAdapter:
    """Test DatabaseAdapter abstract base class."""
    
    @pytest.fixture
    def config(self):
        """Create a test connection config."""
        return ConnectionConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_password"
        )
    
    @pytest.fixture
    def adapter(self, config):
        """Create a mock adapter instance."""
        return MockDatabaseAdapter(config)
    
    @pytest.mark.asyncio
    async def test_adapter_initialization(self, adapter):
        """Test adapter initialization."""
        assert adapter.config.host == "localhost"
        assert adapter.config.port == 5432
        assert adapter.database_type == DatabaseType.POSTGRESQL
        assert adapter.is_connected is False
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, adapter):
        """Test connection and disconnection."""
        # Test connection
        result = await adapter.connect()
        assert result is True
        assert adapter.is_connected is True
        
        # Test disconnection
        result = await adapter.disconnect()
        assert result is True
        assert adapter.is_connected is False
    
    @pytest.mark.asyncio
    async def test_execute_query(self, adapter):
        """Test query execution."""
        await adapter.connect()
        
        result = await adapter.execute_query("SELECT * FROM test")
        
        assert isinstance(result, QueryResult)
        assert result.row_count == 2
        assert len(result.columns) == 2
        assert result.columns == ["id", "name"]
        assert result.execution_time > 0
        assert result.query_id is not None
        assert isinstance(result.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_execute_query_without_connection(self, adapter):
        """Test query execution without connection raises error."""
        with pytest.raises(ConnectionError):
            await adapter.execute_query("SELECT * FROM test")
    
    @pytest.mark.asyncio
    async def test_execute_batch(self, adapter):
        """Test batch query execution."""
        await adapter.connect()
        
        queries = ["SELECT * FROM table1", "SELECT * FROM table2"]
        results = await adapter.execute_batch(queries)
        
        assert len(results) == 2
        assert all(isinstance(result, QueryResult) for result in results)
    
    @pytest.mark.asyncio
    async def test_get_schema(self, adapter):
        """Test schema retrieval."""
        await adapter.connect()
        
        schema = await adapter.get_schema()
        
        assert isinstance(schema, DatabaseSchema)
        assert schema.database_name == "test_db"
        assert len(schema.tables) == 1
        assert schema.tables[0].name == "test_table"
    
    @pytest.mark.asyncio
    async def test_get_table_info(self, adapter):
        """Test table info retrieval."""
        await adapter.connect()
        
        table_info = await adapter.get_table_info("test_table")
        
        assert isinstance(table_info, TableInfo)
        assert table_info.name == "test_table"
        assert table_info.schema == "public"
        assert len(table_info.columns) == 2
    
    @pytest.mark.asyncio
    async def test_get_table_info_not_found(self, adapter):
        """Test table info retrieval for non-existent table."""
        await adapter.connect()
        
        with pytest.raises(SchemaError):
            await adapter.get_table_info("non_existent_table")
    
    @pytest.mark.asyncio
    async def test_get_table_data(self, adapter):
        """Test table data retrieval."""
        await adapter.connect()
        
        result = await adapter.get_table_data("test_table", limit=10, offset=0)
        
        assert isinstance(result, QueryResult)
        assert result.row_count == 2
    
    @pytest.mark.asyncio
    async def test_validate_query(self, adapter):
        """Test query validation."""
        # Valid queries
        assert await adapter.validate_query("SELECT * FROM users") is True
        assert await adapter.validate_query("INSERT INTO users VALUES (1, 'test')") is True
        assert await adapter.validate_query("UPDATE users SET name = 'test'") is True
        
        # Invalid queries
        assert await adapter.validate_query("INVALID SQL") is False
        assert await adapter.validate_query("") is False
    
    @pytest.mark.asyncio
    async def test_get_query_plan(self, adapter):
        """Test query plan retrieval."""
        await adapter.connect()
        
        plan = await adapter.get_query_plan("SELECT * FROM users")
        
        assert isinstance(plan, QueryPlan)
        assert plan.plan_type == "mock_plan"
        assert plan.cost == 1.0
        assert plan.rows_estimated == 100
    
    @pytest.mark.asyncio
    async def test_test_connection(self, adapter):
        """Test connection testing."""
        # Test when not connected
        assert await adapter.test_connection() is False
        
        # Test when connected
        await adapter.connect()
        assert await adapter.test_connection() is True
    
    @pytest.mark.asyncio
    async def test_get_version(self, adapter):
        """Test version retrieval."""
        version = await adapter.version
        assert version == "Mock DB 1.0.0"
    
    @pytest.mark.asyncio
    async def test_get_table_names(self, adapter):
        """Test table names retrieval."""
        await adapter.connect()
        
        table_names = await adapter.get_table_names()
        assert table_names == ["test_table"]
        
        # Test with schema filter
        table_names = await adapter.get_table_names("public")
        assert table_names == ["test_table"]
    
    @pytest.mark.asyncio
    async def test_get_column_names(self, adapter):
        """Test column names retrieval."""
        await adapter.connect()
        
        column_names = await adapter.get_column_names("test_table")
        assert column_names == ["id", "name"]
    
    @pytest.mark.asyncio
    async def test_get_table_size(self, adapter):
        """Test table size retrieval."""
        await adapter.connect()
        
        size = await adapter.get_table_size("test_table")
        assert size == 8192
    
    @pytest.mark.asyncio
    async def test_get_table_row_count(self, adapter):
        """Test table row count retrieval."""
        await adapter.connect()
        
        row_count = await adapter.get_table_row_count("test_table")
        assert row_count == 100
    
    def test_generate_query_id(self, adapter):
        """Test query ID generation."""
        query_id = adapter._generate_query_id()
        assert query_id.startswith("postgresql_")
        assert len(query_id) > 20  # Should include timestamp
    
    def test_sanitize_query(self, adapter):
        """Test query sanitization."""
        # Test comment removal
        query = "SELECT * FROM users -- This is a comment"
        sanitized = adapter._sanitize_query(query)
        assert "-- This is a comment" not in sanitized
        
        # Test block comment removal
        query = "SELECT * FROM users /* This is a block comment */ WHERE id = 1"
        sanitized = adapter._sanitize_query(query)
        assert "/* This is a block comment */" not in sanitized
        
        # Test whitespace normalization
        query = "SELECT   *   FROM\nusers\tWHERE\n\tid = 1"
        sanitized = adapter._sanitize_query(query)
        assert "\n" not in sanitized
        assert "\t" not in sanitized
        assert "  " not in sanitized  # Multiple spaces should be normalized
    
    @pytest.mark.asyncio
    async def test_context_manager(self, adapter):
        """Test async context manager functionality."""
        async with adapter as ctx_adapter:
            assert ctx_adapter.is_connected is True
            assert ctx_adapter is adapter
        
        # Should be disconnected after context exit
        assert adapter.is_connected is False


class TestDatabaseAdapterExceptions:
    """Test database adapter exceptions."""
    
    def test_database_adapter_error(self):
        """Test DatabaseAdapterError."""
        error = DatabaseAdapterError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_connection_error(self):
        """Test ConnectionError."""
        error = ConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, DatabaseAdapterError)
    
    def test_query_execution_error(self):
        """Test QueryExecutionError."""
        error = QueryExecutionError("Query failed")
        assert str(error) == "Query failed"
        assert isinstance(error, DatabaseAdapterError)
    
    def test_schema_error(self):
        """Test SchemaError."""
        error = SchemaError("Schema error")
        assert str(error) == "Schema error"
        assert isinstance(error, DatabaseAdapterError)
    
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, DatabaseAdapterError)


if __name__ == "__main__":
    pytest.main([__file__])
