"""
Unit tests for SQL Server Database Adapter

Tests the SQLServerAdapter implementation with comprehensive coverage.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime
import pyodbc

from adapters.sqlserver_adapter import SQLServerAdapter, SQLServerConnectionPool
from adapters.database_adapter import (
    ConnectionConfig, DatabaseType, QueryResult, ColumnInfo,
    TableInfo, DatabaseSchema, QueryPlan, ForeignKeyInfo, IndexInfo
)


class TestSQLServerAdapter:
    """Test cases for SQLServerAdapter"""
    
    @pytest.fixture
    def config(self):
        """Create test connection configuration"""
        return ConnectionConfig(
            host="localhost",
            port=1433,
            database="test_db",
            username="test_user",
            password="test_password",
            driver="ODBC Driver 17 for SQL Server",
            connection_timeout=30,
            pool_size=5,
            max_overflow=10
        )
    
    @pytest.fixture
    def adapter(self, config):
        """Create SQL Server adapter instance"""
        return SQLServerAdapter(config)
    
    def test_database_type(self, adapter):
        """Test database type property"""
        assert adapter.database_type == DatabaseType.SQLSERVER
    
    def test_initialization(self, adapter, config):
        """Test adapter initialization"""
        assert adapter.config == config
        assert adapter._driver == "ODBC Driver 17 for SQL Server"
        assert adapter._trusted_connection is False
        assert adapter.is_connected is False
        assert adapter._pool is None
    
    def test_trusted_connection_detection(self):
        """Test Windows Authentication detection"""
        config = ConnectionConfig(
            host="localhost",
            port=1433,
            database="test_db",
            username="",
            password=""
        )
        adapter = SQLServerAdapter(config)
        assert adapter._trusted_connection is True
    
    @pytest.mark.asyncio
    async def test_connect_success(self, adapter):
        """Test successful connection"""
        with patch('pyodbc.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(adapter, '_initialize_pool') as mock_init_pool:
                result = await adapter.connect()
                
                assert result is True
                assert adapter.is_connected is True
                mock_connect.assert_called_once()
                mock_init_pool.assert_called_once()
                mock_conn.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, adapter):
        """Test connection failure"""
        with patch('pyodbc.connect', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception):
                await adapter.connect()
            
            assert adapter.is_connected is False
    
    @pytest.mark.asyncio
    async def test_disconnect_success(self, adapter):
        """Test successful disconnection"""
        adapter.is_connected = True
        mock_pool = MagicMock()
        adapter._pool = mock_pool

        result = await adapter.disconnect()

        assert result is True
        assert adapter.is_connected is False
        mock_pool.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_failure(self, adapter):
        """Test disconnection failure"""
        adapter.is_connected = True
        adapter._pool = MagicMock()
        adapter._pool.close.side_effect = Exception("Close failed")
        
        result = await adapter.disconnect()
        
        assert result is False
        assert adapter.is_connected is False
    
    @pytest.mark.asyncio
    async def test_execute_query_success(self, adapter):
        """Test successful query execution"""
        adapter.is_connected = True
        adapter._pool = MagicMock()
        
        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [('id',), ('name',)]
        mock_cursor.fetchall.return_value = [(1, 'John'), (2, 'Jane')]
        
        adapter._pool.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        result = await adapter.execute_query("SELECT * FROM users")
        
        assert isinstance(result, QueryResult)
        assert result.row_count == 2
        assert result.columns == ['id', 'name']
        assert result.data == [{'id': 1, 'name': 'John'}, {'id': 2, 'name': 'Jane'}]
        assert result.query_id is not None
        assert result.timestamp is not None
        assert result.metadata['database'] == 'sqlserver'
        assert result.metadata['query_type'] == 'SELECT'
        
        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()
        adapter._pool.return_connection.assert_called_once_with(mock_conn)
    
    @pytest.mark.asyncio
    async def test_execute_query_with_params(self, adapter):
        """Test query execution with parameters"""
        adapter.is_connected = True
        adapter._pool = MagicMock()
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [('id',)]
        mock_cursor.fetchall.return_value = [(1,)]
        
        adapter._pool.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        params = {'user_id': 1}
        result = await adapter.execute_query("SELECT * FROM users WHERE id = ?", params)
        
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users WHERE id = ?", params)
        assert result.row_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self, adapter):
        """Test query execution when not connected"""
        adapter.is_connected = False
        
        with pytest.raises(Exception):
            await adapter.execute_query("SELECT * FROM users")
    
    @pytest.mark.asyncio
    async def test_execute_query_error(self, adapter):
        """Test query execution error handling"""
        adapter.is_connected = True
        adapter._pool = MagicMock()
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Query failed")
        
        adapter._pool.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        result = await adapter.execute_query("SELECT * FROM users")
        
        assert result.error == "Query failed"
        assert result.row_count == 0
        assert result.data == []
    
    @pytest.mark.asyncio
    async def test_execute_batch(self, adapter):
        """Test batch query execution"""
        adapter.is_connected = True
        
        with patch.object(adapter, 'execute_query') as mock_execute:
            mock_execute.side_effect = [
                QueryResult(data=[{'count': 5}], columns=['count'], row_count=1, 
                           execution_time=0.1, query_id="1", timestamp=datetime.utcnow()),
                QueryResult(data=[{'count': 10}], columns=['count'], row_count=1, 
                           execution_time=0.1, query_id="2", timestamp=datetime.utcnow())
            ]
            
            queries = ["SELECT COUNT(*) FROM users", "SELECT COUNT(*) FROM orders"]
            results = await adapter.execute_batch(queries)
            
            assert len(results) == 2
            assert results[0].data[0]['count'] == 5
            assert results[1].data[0]['count'] == 10
            assert mock_execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_schema_success(self, adapter):
        """Test successful schema retrieval"""
        adapter.is_connected = True
        
        # Mock table info
        mock_table = TableInfo(
            name="users",
            schema="dbo",
            columns=[],
            primary_keys=[],
            foreign_keys=[],
            indexes=[],
            row_count=100,
            size_bytes=1024,
            business_domain="crm"
        )
        
        with patch.object(adapter, 'execute_query') as mock_execute:
            # Mock tables query
            mock_execute.side_effect = [
                QueryResult(data=[{'TABLE_NAME': 'users', 'TABLE_SCHEMA': 'dbo'}], 
                           columns=['TABLE_NAME', 'TABLE_SCHEMA'], row_count=1, 
                           execution_time=0.1, query_id="1", timestamp=datetime.utcnow()),
                # Mock views query
                QueryResult(data=[], columns=[], row_count=0, 
                           execution_time=0.1, query_id="2", timestamp=datetime.utcnow()),
                # Mock functions query
                QueryResult(data=[], columns=[], row_count=0, 
                           execution_time=0.1, query_id="3", timestamp=datetime.utcnow())
            ]
            
            with patch.object(adapter, 'get_table_info', return_value=mock_table):
                with patch.object(adapter, '_get_version', return_value="SQL Server 2019"):
                    schema = await adapter.get_schema()
                    
                    assert isinstance(schema, DatabaseSchema)
                    assert schema.database_name == "test_db"
                    assert len(schema.tables) == 1
                    assert schema.tables[0].name == "users"
                    assert schema.version == "SQL Server 2019"
    
    @pytest.mark.asyncio
    async def test_get_table_info_success(self, adapter):
        """Test successful table info retrieval"""
        adapter.is_connected = True
        
        with patch.object(adapter, 'execute_query') as mock_execute:
            # Mock columns query
            mock_execute.side_effect = [
                QueryResult(data=[
                    {'COLUMN_NAME': 'id', 'DATA_TYPE': 'int', 'IS_NULLABLE': 'NO', 
                     'COLUMN_DEFAULT': None, 'CHARACTER_MAXIMUM_LENGTH': None,
                     'NUMERIC_PRECISION': 10, 'NUMERIC_SCALE': 0, 'IS_IDENTITY': 1, 'DESCRIPTION': None}
                ], columns=['COLUMN_NAME', 'DATA_TYPE'], row_count=1, 
                execution_time=0.1, query_id="1", timestamp=datetime.utcnow()),
                # Mock primary keys query
                QueryResult(data=[{'COLUMN_NAME': 'id'}], columns=['COLUMN_NAME'], 
                           row_count=1, execution_time=0.1, query_id="2", timestamp=datetime.utcnow()),
                # Mock foreign keys query
                QueryResult(data=[], columns=[], row_count=0, 
                           execution_time=0.1, query_id="3", timestamp=datetime.utcnow()),
                # Mock indexes query
                QueryResult(data=[], columns=[], row_count=0, 
                           execution_time=0.1, query_id="4", timestamp=datetime.utcnow()),
                # Mock stats query
                QueryResult(data=[{'ROW_COUNT': 100, 'SIZE_BYTES': 1024}], 
                           columns=['ROW_COUNT', 'SIZE_BYTES'], row_count=1, 
                           execution_time=0.1, query_id="5", timestamp=datetime.utcnow())
            ]
            
            table_info = await adapter.get_table_info("users", "dbo")
            
            assert isinstance(table_info, TableInfo)
            assert table_info.name == "users"
            assert table_info.schema == "dbo"
            assert len(table_info.columns) == 1
            assert table_info.columns[0].name == "id"
            assert table_info.columns[0].data_type == "int"
            assert table_info.row_count == 100
            assert table_info.size_bytes == 1024
    
    @pytest.mark.asyncio
    async def test_get_table_data(self, adapter):
        """Test table data retrieval"""
        adapter.is_connected = True
        
        with patch.object(adapter, 'execute_query') as mock_execute:
            mock_execute.return_value = QueryResult(
                data=[{'id': 1, 'name': 'John'}], 
                columns=['id', 'name'], 
                row_count=1, 
                execution_time=0.1, 
                query_id="1", 
                timestamp=datetime.utcnow()
            )
            
            result = await adapter.get_table_data("users", limit=10, offset=0, schema="dbo")
            
            assert result.row_count == 1
            assert result.data[0]['id'] == 1
            mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_query_success(self, adapter):
        """Test successful query validation"""
        adapter.is_connected = True
        
        with patch.object(adapter, 'execute_query') as mock_execute:
            mock_execute.return_value = QueryResult(
                data=[], columns=[], row_count=0, 
                execution_time=0.1, query_id="1", timestamp=datetime.utcnow()
            )
            
            result = await adapter.validate_query("SELECT * FROM users")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_query_failure(self, adapter):
        """Test query validation failure"""
        adapter.is_connected = True
        
        with patch.object(adapter, 'execute_query', side_effect=Exception("Invalid query")):
            result = await adapter.validate_query("INVALID SQL")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_query_plan_success(self, adapter):
        """Test successful query plan retrieval"""
        adapter.is_connected = True
        
        with patch.object(adapter, 'execute_query') as mock_execute:
            mock_execute.return_value = QueryResult(
                data=[{'StmtText': '<ShowPlanXML><Batch><Statements><StmtSimple EstimatedTotalSubtreeCost="0.1" EstimatedRows="100">...</StmtSimple></Statements></Batch></ShowPlanXML>'}], 
                columns=['StmtText'], 
                row_count=1, 
                execution_time=0.1, 
                query_id="1", 
                timestamp=datetime.utcnow()
            )
            
            plan = await adapter.get_query_plan("SELECT * FROM users")
            
            assert isinstance(plan, QueryPlan)
            assert plan.plan_type == "SQL Server Execution Plan"
            assert plan.cost == 0.1
            assert plan.rows_estimated == 100
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, adapter):
        """Test successful connection test"""
        adapter.is_connected = True
        
        with patch.object(adapter, 'execute_query') as mock_execute:
            mock_execute.return_value = QueryResult(
                data=[{'test': 1}], columns=['test'], row_count=1, 
                execution_time=0.1, query_id="1", timestamp=datetime.utcnow()
            )
            
            result = await adapter.test_connection()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self, adapter):
        """Test connection test failure"""
        adapter.is_connected = True
        
        with patch.object(adapter, 'execute_query', side_effect=Exception("Connection failed")):
            result = await adapter.test_connection()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_version_success(self, adapter):
        """Test successful version retrieval"""
        with patch.object(adapter, 'execute_query') as mock_execute:
            mock_execute.return_value = QueryResult(
                data=[{'version': 'Microsoft SQL Server 2019'}], 
                columns=['version'], row_count=1, 
                execution_time=0.1, query_id="1", timestamp=datetime.utcnow()
            )
            
            version = await adapter._get_version()
            assert version == "Microsoft SQL Server 2019"
    
    def test_build_connection_string_sql_auth(self, adapter):
        """Test connection string building with SQL authentication"""
        conn_str = adapter._build_connection_string()
        
        assert "DRIVER={ODBC Driver 17 for SQL Server}" in conn_str
        assert "SERVER=localhost,1433" in conn_str
        assert "DATABASE=test_db" in conn_str
        assert "UID=test_user" in conn_str
        assert "PWD=test_password" in conn_str
        assert "Trusted_Connection=yes" not in conn_str
    
    def test_build_connection_string_trusted_auth(self):
        """Test connection string building with Windows authentication"""
        config = ConnectionConfig(
            host="localhost",
            port=1433,
            database="test_db",
            username="",
            password=""
        )
        adapter = SQLServerAdapter(config)
        adapter._trusted_connection = True
        
        conn_str = adapter._build_connection_string()
        
        assert "Trusted_Connection=yes" in conn_str
        assert "UID=" not in conn_str
        assert "PWD=" not in conn_str
    
    def test_build_connection_string_ssl(self, adapter):
        """Test connection string building with SSL settings"""
        adapter.config.ssl_mode = "require"
        conn_str = adapter._build_connection_string()
        
        assert "Encrypt=yes" in conn_str
        assert "TrustServerCertificate=no" in conn_str
    
    def test_get_query_type(self, adapter):
        """Test query type detection"""
        assert adapter._get_query_type("SELECT * FROM users") == "SELECT"
        assert adapter._get_query_type("INSERT INTO users VALUES (1, 'John')") == "INSERT"
        assert adapter._get_query_type("UPDATE users SET name = 'Jane'") == "UPDATE"
        assert adapter._get_query_type("DELETE FROM users") == "DELETE"
        assert adapter._get_query_type("CREATE TABLE users") == "CREATE"
        assert adapter._get_query_type("ALTER TABLE users ADD COLUMN email") == "ALTER"
        assert adapter._get_query_type("DROP TABLE users") == "DROP"
        assert adapter._get_query_type("EXEC sp_help") == "OTHER"
    
    def test_detect_business_domain(self, adapter):
        """Test business domain detection"""
        # Test CRM domain
        columns = [ColumnInfo(name="customer_id", data_type="int", is_nullable=False)]
        assert adapter._detect_business_domain("customers", columns) == "crm"
        
        # Test finance domain
        columns = [ColumnInfo(name="account_id", data_type="int", is_nullable=False)]
        assert adapter._detect_business_domain("accounts", columns) == "finance"
        
        # Test e-commerce domain
        columns = [ColumnInfo(name="product_id", data_type="int", is_nullable=False)]
        assert adapter._detect_business_domain("products", columns) == "ecommerce"
        
        # Test procurement domain
        columns = [ColumnInfo(name="vendor_id", data_type="int", is_nullable=False)]
        assert adapter._detect_business_domain("vendors", columns) == "procurement"
        
        # Test general domain
        columns = [ColumnInfo(name="id", data_type="int", is_nullable=False)]
        assert adapter._detect_business_domain("misc_table", columns) == "general"
    
    def test_extract_plan_cost(self, adapter):
        """Test execution plan cost extraction"""
        plan_xml = '<StmtSimple EstimatedTotalSubtreeCost="0.123456">...</StmtSimple>'
        cost = adapter._extract_plan_cost(plan_xml)
        assert cost == 0.123456
        
        # Test with invalid XML
        cost = adapter._extract_plan_cost("invalid xml")
        assert cost is None
    
    def test_extract_plan_rows(self, adapter):
        """Test execution plan rows extraction"""
        plan_xml = '<StmtSimple EstimatedRows="1000">...</StmtSimple>'
        rows = adapter._extract_plan_rows(plan_xml)
        assert rows == 1000
        
        # Test with invalid XML
        rows = adapter._extract_plan_rows("invalid xml")
        assert rows is None


class TestSQLServerConnectionPool:
    """Test cases for SQLServerConnectionPool"""
    
    @pytest.fixture
    def pool(self):
        """Create connection pool instance"""
        return SQLServerConnectionPool(
            connection_string="DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=test;",
            pool_size=2,
            max_overflow=1,
            timeout=30
        )
    
    @pytest.mark.asyncio
    async def test_get_connection_new(self, pool):
        """Test getting new connection from pool"""
        with patch('pyodbc.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            connection = await pool.get_connection()
            
            assert connection == mock_conn
            assert pool._created_connections == 1
            mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_connection_existing(self, pool):
        """Test getting existing connection from pool"""
        mock_conn = MagicMock()
        await pool._pool.put(mock_conn)
        
        connection = await pool.get_connection()
        
        assert connection == mock_conn
        assert pool._created_connections == 0
    
    @pytest.mark.asyncio
    async def test_return_connection_success(self, pool):
        """Test returning connection to pool"""
        mock_conn = MagicMock()
        
        await pool.return_connection(mock_conn)
        
        assert pool._pool.qsize() == 1
    
    @pytest.mark.asyncio
    async def test_return_connection_pool_full(self, pool):
        """Test returning connection when pool is full"""
        # Fill the pool
        for _ in range(pool.pool_size + pool.max_overflow):
            await pool._pool.put(MagicMock())
        
        mock_conn = MagicMock()
        await pool.return_connection(mock_conn)
        
        # Connection should be closed
        mock_conn.close.assert_called_once()
        assert pool._created_connections == 0
    
    def test_close(self, pool):
        """Test closing all connections in pool"""
        # Add some mock connections
        mock_conn1 = MagicMock()
        mock_conn2 = MagicMock()
        
        asyncio.run(pool._pool.put(mock_conn1))
        asyncio.run(pool._pool.put(mock_conn2))
        
        pool.close()
        
        mock_conn1.close.assert_called_once()
        mock_conn2.close.assert_called_once()
        assert pool._created_connections == 0


@pytest.mark.asyncio
async def test_adapter_context_manager():
    """Test adapter as context manager"""
    config = ConnectionConfig(
        host="localhost",
        port=1433,
        database="test_db",
        username="test_user",
        password="test_password"
    )
    
    with patch('pyodbc.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        with patch.object(SQLServerAdapter, '_initialize_pool'):
            async with SQLServerAdapter(config) as adapter:
                assert adapter.is_connected is True
            
            # Connection should be closed after context
            assert adapter.is_connected is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
