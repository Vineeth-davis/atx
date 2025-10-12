"""
SQL Server Database Adapter

A production-ready adapter for Microsoft SQL Server using pyodbc.
Provides full support for SQL Server-specific features and optimizations.
"""

import asyncio
import logging
import pyodbc
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid
import re

from .database_adapter import (
    DatabaseAdapter,
    DatabaseType,
    ConnectionConfig,
    QueryResult,
    ColumnInfo,
    TableInfo,
    DatabaseSchema,
    QueryPlan,
    ForeignKeyInfo,
    IndexInfo,
    ConnectionError,
    QueryExecutionError,
    SchemaError,
    ValidationError
)

logger = logging.getLogger(__name__)


class SQLServerAdapter(DatabaseAdapter):
    """
    SQL Server database adapter using pyodbc.
    
    Features:
    - Full SQL Server support (2016+)
    - Connection pooling
    - Schema introspection
    - Query execution with parameters
    - Transaction support
    - Performance optimization
    """
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self._connection_string = None
        self._pool = None
        self._driver = config.driver or "ODBC Driver 17 for SQL Server"
        # Check if using Windows Authentication
        self._trusted_connection = (config.username == '' or config.password == '')
        
    @property
    def database_type(self) -> DatabaseType:
        return DatabaseType.SQLSERVER
    
    async def connect(self) -> bool:
        """
        Establish connection to SQL Server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Build connection string
            self._connection_string = self._build_connection_string()
            
            # Test connection
            test_conn = pyodbc.connect(self._connection_string, timeout=self.config.connection_timeout)
            test_conn.close()
            
            # Initialize connection pool
            await self._initialize_pool()
            
            self.is_connected = True
            logger.info(f"Successfully connected to SQL Server: {self.config.host}:{self.config.port}/{self.config.database}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to SQL Server: {e}")
            self.is_connected = False
            raise ConnectionError(f"Failed to connect to SQL Server: {e}")
    
    async def disconnect(self) -> bool:
        """
        Close SQL Server connection and cleanup pool.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        try:
            if self._pool:
                self._pool.close()
                self._pool = None
            
            self.is_connected = False
            logger.info("Disconnected from SQL Server")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from SQL Server: {e}")
            self.is_connected = False  # Ensure we mark as disconnected even on error
            return False
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> QueryResult:
        """
        Execute SQL query and return results.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            QueryResult: Query execution results
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to database")
        
        start_time = datetime.utcnow()
        query_id = self._generate_query_id()
        
        try:
            # Sanitize query
            sanitized_query = self._sanitize_query(query)
            
            # Get connection from pool
            conn = await self._pool.get_connection()
            cursor = conn.cursor()
            
            try:
                # Execute query with parameters
                if params:
                    cursor.execute(sanitized_query, params)
                else:
                    cursor.execute(sanitized_query)
                
                # Fetch results
                columns = [column[0] for column in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                
                # Convert rows to dictionaries
                data = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        # Handle SQL Server specific data types
                        if isinstance(value, datetime):
                            row_dict[columns[i]] = value.isoformat()
                        elif isinstance(value, (bytes, bytearray)):
                            row_dict[columns[i]] = value.hex()
                        else:
                            row_dict[columns[i]] = value
                    data.append(row_dict)
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                return QueryResult(
                    data=data,
                    columns=columns,
                    row_count=len(data),
                    execution_time=execution_time,
                    query_id=query_id,
                    timestamp=start_time,
                    metadata={
                        "database": "sqlserver",
                        "query_type": self._get_query_type(sanitized_query),
                        "server": f"{self.config.host}:{self.config.port}",
                        "database_name": self.config.database
                    }
                )
                
            finally:
                cursor.close()
                await self._pool.return_connection(conn)
                
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Query execution failed: {e}")
            
            return QueryResult(
                data=[],
                columns=[],
                row_count=0,
                execution_time=execution_time,
                query_id=query_id,
                timestamp=start_time,
                metadata={"database": "sqlserver", "error": str(e)},
                error=str(e)
            )
    
    async def execute_batch(self, queries: List[str]) -> List[QueryResult]:
        """
        Execute multiple queries in batch.
        
        Args:
            queries: List of SQL query strings
            
        Returns:
            List[QueryResult]: Results for each query
        """
        results = []
        for query in queries:
            result = await self.execute_query(query)
            results.append(result)
        return results
    
    async def get_schema(self, force_refresh: bool = False) -> DatabaseSchema:
        """
        Get complete database schema.
        
        Args:
            force_refresh: Force refresh of cached schema
            
        Returns:
            DatabaseSchema: Complete database schema information
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to database")
        
        # Check cache
        if not force_refresh and self._schema_cache and self._last_schema_refresh:
            cache_age = (datetime.utcnow() - self._last_schema_refresh).total_seconds()
            if cache_age < 300:  # 5 minutes cache
                return self._schema_cache
        
        try:
            # Get tables
            tables_query = """
            SELECT 
                t.TABLE_SCHEMA,
                t.TABLE_NAME,
                t.TABLE_TYPE,
                p.rows as ROW_COUNT,
                SUM(a.total_pages) * 8 as SIZE_BYTES
            FROM INFORMATION_SCHEMA.TABLES t
            LEFT JOIN sys.partitions p ON t.TABLE_NAME = OBJECT_NAME(p.object_id)
            LEFT JOIN sys.allocation_units a ON p.partition_id = a.container_id
            WHERE t.TABLE_TYPE = 'BASE TABLE'
            GROUP BY t.TABLE_SCHEMA, t.TABLE_NAME, t.TABLE_TYPE, p.rows
            ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME
            """
            
            tables_result = await self.execute_query(tables_query)
            tables = []
            
            for row in tables_result.data:
                table_name = row['TABLE_NAME']
                schema_name = row['TABLE_SCHEMA']
                
                # Get table info
                table_info = await self.get_table_info(table_name, schema_name)
                tables.append(table_info)
            
            # Get views
            views_query = """
            SELECT 
                TABLE_SCHEMA,
                TABLE_NAME,
                TABLE_TYPE
            FROM INFORMATION_SCHEMA.VIEWS
            ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            
            views_result = await self.execute_query(views_query)
            views = []
            
            for row in views_result.data:
                view_name = row['TABLE_NAME']
                schema_name = row['TABLE_SCHEMA']
                
                # Get view info (similar to table)
                view_info = await self.get_table_info(view_name, schema_name)
                views.append(view_info)
            
            # Get functions and procedures
            functions_query = """
            SELECT 
                ROUTINE_SCHEMA,
                ROUTINE_NAME,
                ROUTINE_TYPE
            FROM INFORMATION_SCHEMA.ROUTINES
            WHERE ROUTINE_TYPE IN ('FUNCTION', 'PROCEDURE')
            ORDER BY ROUTINE_SCHEMA, ROUTINE_NAME
            """
            
            functions_result = await self.execute_query(functions_query)
            functions = []
            procedures = []
            
            for row in functions_result.data:
                if row['ROUTINE_TYPE'] == 'FUNCTION':
                    functions.append(f"{row['ROUTINE_SCHEMA']}.{row['ROUTINE_NAME']}")
                else:
                    procedures.append(f"{row['ROUTINE_SCHEMA']}.{row['ROUTINE_NAME']}")
            
            # Calculate total size
            total_size = sum(table.size_bytes for table in tables)
            
            schema = DatabaseSchema(
                database_name=self.config.database,
                tables=tables,
                views=views,
                functions=functions,
                procedures=procedures,
                total_size_bytes=total_size,
                version=await self._get_version(),
                description=f"SQL Server database: {self.config.database}"
            )
            
            # Cache schema
            self._schema_cache = schema
            self._last_schema_refresh = datetime.utcnow()
            
            return schema
            
        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            raise SchemaError(f"Failed to get schema: {e}")
    
    async def get_table_info(self, table_name: str, schema: Optional[str] = None) -> TableInfo:
        """
        Get detailed information about a specific table.
        
        Args:
            table_name: Name of the table
            schema: Optional schema name (defaults to 'dbo')
            
        Returns:
            TableInfo: Detailed table information
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to database")
        
        schema_name = schema or 'dbo'
        
        try:
            # Get table columns
            columns_query = """
            SELECT 
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.IS_NULLABLE,
                c.COLUMN_DEFAULT,
                c.CHARACTER_MAXIMUM_LENGTH,
                c.NUMERIC_PRECISION,
                c.NUMERIC_SCALE,
                COLUMNPROPERTY(OBJECT_ID(QUOTENAME(c.TABLE_SCHEMA) + '.' + QUOTENAME(c.TABLE_NAME)), c.COLUMN_NAME, 'IsIdentity') as IS_IDENTITY,
                ep.value as DESCRIPTION
            FROM INFORMATION_SCHEMA.COLUMNS c
            LEFT JOIN sys.extended_properties ep ON 
                ep.major_id = OBJECT_ID(QUOTENAME(c.TABLE_SCHEMA) + '.' + QUOTENAME(c.TABLE_NAME)) AND
                ep.minor_id = c.ORDINAL_POSITION AND
                ep.name = 'MS_Description'
            WHERE c.TABLE_NAME = ? AND c.TABLE_SCHEMA = ?
            ORDER BY c.ORDINAL_POSITION
            """
            
            columns_result = await self.execute_query(columns_query, (table_name, schema_name))
            
            # Get primary keys
            pk_query = """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_NAME = ? AND TABLE_SCHEMA = ? AND CONSTRAINT_NAME LIKE 'PK_%'
            ORDER BY ORDINAL_POSITION
            """
            
            pk_result = await self.execute_query(pk_query, (table_name, schema_name))
            primary_keys = [row['COLUMN_NAME'] for row in pk_result.data]
            
            # Get foreign keys
            fk_query = """
            SELECT 
                kcu.COLUMN_NAME,
                ccu.TABLE_NAME as REFERENCED_TABLE,
                ccu.COLUMN_NAME as REFERENCED_COLUMN,
                tc.CONSTRAINT_NAME,
                rc.DELETE_RULE,
                rc.UPDATE_RULE
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc ON kcu.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc ON tc.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu ON rc.UNIQUE_CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
            WHERE kcu.TABLE_NAME = ? AND kcu.TABLE_SCHEMA = ? AND tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
            """
            
            fk_result = await self.execute_query(fk_query, (table_name, schema_name))
            foreign_keys = []
            
            for row in fk_result.data:
                fk = ForeignKeyInfo(
                    column_name=row['COLUMN_NAME'],
                    referenced_table=row['REFERENCED_TABLE'],
                    referenced_column=row['REFERENCED_COLUMN'],
                    constraint_name=row['CONSTRAINT_NAME'],
                    on_delete=row['DELETE_RULE'],
                    on_update=row['UPDATE_RULE']
                )
                foreign_keys.append(fk)
            
            # Get indexes
            indexes_query = """
            SELECT 
                i.name as INDEX_NAME,
                c.name as COLUMN_NAME,
                i.is_unique,
                i.is_primary_key,
                i.type_desc,
                i.fill_factor
            FROM sys.indexes i
            JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE i.object_id = OBJECT_ID(QUOTENAME(?) + '.' + QUOTENAME(?))
            ORDER BY i.name, ic.key_ordinal
            """
            
            indexes_result = await self.execute_query(indexes_query, (schema_name, table_name))
            
            # Group indexes
            index_dict = {}
            for row in indexes_result.data:
                index_name = row['INDEX_NAME']
                if index_name not in index_dict:
                    index_dict[index_name] = {
                        'name': index_name,
                        'columns': [],
                        'is_unique': bool(row['is_unique']),
                        'is_primary': bool(row['is_primary_key']),
                        'is_clustered': row['type_desc'] == 'CLUSTERED',
                        'fill_factor': row['fill_factor']
                    }
                index_dict[index_name]['columns'].append(row['COLUMN_NAME'])
            
            indexes = []
            for index_info in index_dict.values():
                index = IndexInfo(
                    name=index_info['name'],
                    columns=index_info['columns'],
                    is_unique=index_info['is_unique'],
                    is_primary=index_info['is_primary'],
                    is_clustered=index_info['is_clustered'],
                    fill_factor=index_info['fill_factor']
                )
                indexes.append(index)
            
            # Get row count and size
            stats_query = """
            SELECT 
                p.rows as ROW_COUNT,
                SUM(a.total_pages) * 8 as SIZE_BYTES
            FROM sys.partitions p
            JOIN sys.allocation_units a ON p.partition_id = a.container_id
            WHERE p.object_id = OBJECT_ID(QUOTENAME(?) + '.' + QUOTENAME(?))
            GROUP BY p.rows
            """
            
            stats_result = await self.execute_query(stats_query, (schema_name, table_name))
            row_count = stats_result.data[0]['ROW_COUNT'] if stats_result.data else 0
            size_bytes = stats_result.data[0]['SIZE_BYTES'] if stats_result.data else 0
            
            # Build columns list
            columns = []
            for row in columns_result.data:
                column = ColumnInfo(
                    name=row['COLUMN_NAME'],
                    data_type=row['DATA_TYPE'],
                    is_nullable=row['IS_NULLABLE'] == 'YES',
                    default_value=row['COLUMN_DEFAULT'],
                    max_length=row['CHARACTER_MAXIMUM_LENGTH'],
                    precision=row['NUMERIC_PRECISION'],
                    scale=row['NUMERIC_SCALE'],
                    is_primary_key=row['COLUMN_NAME'] in primary_keys,
                    is_foreign_key=any(fk.column_name == row['COLUMN_NAME'] for fk in foreign_keys),
                    is_unique=row['COLUMN_NAME'] in primary_keys,  # Simplified
                    is_indexed=any(row['COLUMN_NAME'] in idx.columns for idx in indexes),
                    description=row['DESCRIPTION']
                )
                columns.append(column)
            
            # Detect business domain
            business_domain = self._detect_business_domain(table_name, columns)
            
            return TableInfo(
                name=table_name,
                schema=schema_name,
                columns=columns,
                primary_keys=primary_keys,
                foreign_keys=foreign_keys,
                indexes=indexes,
                row_count=row_count,
                size_bytes=size_bytes,
                description=f"SQL Server table: {schema_name}.{table_name}",
                business_domain=business_domain
            )
            
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            raise SchemaError(f"Failed to get table info for {table_name}: {e}")
    
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
        schema_name = schema or 'dbo'
        query = f"SELECT * FROM [{schema_name}].[{table_name}] ORDER BY (SELECT NULL) OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
        return await self.execute_query(query)
    
    async def validate_query(self, query: str) -> bool:
        """
        Validate SQL query syntax.
        
        Args:
            query: SQL query string to validate
            
        Returns:
            bool: True if query is valid, False otherwise
        """
        if not self.is_connected:
            return False
        
        try:
            # Use SQL Server's built-in validation
            validation_query = f"SET PARSEONLY ON; {query}; SET PARSEONLY OFF;"
            await self.execute_query(validation_query)
            return True
            
        except Exception:
            return False
    
    async def get_query_plan(self, query: str) -> QueryPlan:
        """
        Get query execution plan.
        
        Args:
            query: SQL query string
            
        Returns:
            QueryPlan: Query execution plan information
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to database")
        
        try:
            # Get execution plan
            plan_query = f"SET SHOWPLAN_XML ON; {query}; SET SHOWPLAN_XML OFF;"
            plan_result = await self.execute_query(plan_query)
            
            if plan_result.data:
                plan_xml = plan_result.data[0].get('StmtText', '')
                
                # Parse plan for basic info
                cost = self._extract_plan_cost(plan_xml)
                rows_estimated = self._extract_plan_rows(plan_xml)
                
                return QueryPlan(
                    plan_type="SQL Server Execution Plan",
                    cost=cost,
                    rows_estimated=rows_estimated,
                    execution_time=None,
                    details={
                        "plan_xml": plan_xml,
                        "database": "sqlserver",
                        "server": f"{self.config.host}:{self.config.port}"
                    }
                )
            else:
                return QueryPlan(
                    plan_type="SQL Server Execution Plan",
                    details={"error": "No plan available"}
                )
                
        except Exception as e:
            logger.error(f"Failed to get query plan: {e}")
            return QueryPlan(
                plan_type="SQL Server Execution Plan",
                details={"error": str(e)}
            )
    
    async def test_connection(self) -> bool:
        """
        Test database connectivity.
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        try:
            result = await self.execute_query("SELECT 1 as test")
            return result.row_count == 1 and result.data[0]['test'] == 1
        except Exception:
            return False
    
    async def _get_version(self) -> str:
        """
        Get SQL Server version.
        
        Returns:
            str: SQL Server version string
        """
        try:
            result = await self.execute_query("SELECT @@VERSION as version")
            if result.data:
                return result.data[0]['version']
            return "Unknown"
        except Exception:
            return "Unknown"
    
    def _build_connection_string(self) -> str:
        """
        Build SQL Server connection string.
        
        Returns:
            str: Connection string for pyodbc
        """
        if self._trusted_connection:
            conn_str = (
                f"DRIVER={{{self._driver}}};"
                f"SERVER={self.config.host},{self.config.port};"
                f"DATABASE={self.config.database};"
                f"Trusted_Connection=yes;"
                f"Connection Timeout={self.config.connection_timeout};"
            )
        else:
            conn_str = (
                f"DRIVER={{{self._driver}}};"
                f"SERVER={self.config.host},{self.config.port};"
                f"DATABASE={self.config.database};"
                f"UID={self.config.username};"
                f"PWD={self.config.password};"
                f"Connection Timeout={self.config.connection_timeout};"
            )
        
        # Add SSL settings if specified
        if self.config.ssl_mode:
            if self.config.ssl_mode.lower() == 'require':
                conn_str += "Encrypt=yes;TrustServerCertificate=no;"
            elif self.config.ssl_mode.lower() == 'prefer':
                conn_str += "Encrypt=yes;TrustServerCertificate=yes;"
            elif self.config.ssl_mode.lower() == 'disable':
                conn_str += "Encrypt=no;"
        else:
            # Default: Trust server certificate for development/testing
            conn_str += "Encrypt=yes;TrustServerCertificate=yes;"
        
        return conn_str
    
    async def _initialize_pool(self):
        """
        Initialize connection pool for SQL Server.
        """
        try:
            # Simple connection pool implementation
            self._pool = SQLServerConnectionPool(
                connection_string=self._connection_string,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                timeout=self.config.connection_timeout
            )
            logger.info(f"Initialized SQL Server connection pool with {self.config.pool_size} connections")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise ConnectionError(f"Failed to initialize connection pool: {e}")
    
    def _get_query_type(self, query: str) -> str:
        """
        Determine query type from SQL statement.
        
        Args:
            query: SQL query string
            
        Returns:
            str: Query type (SELECT, INSERT, UPDATE, DELETE, etc.)
        """
        query_upper = query.strip().upper()
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        elif query_upper.startswith('CREATE'):
            return 'CREATE'
        elif query_upper.startswith('ALTER'):
            return 'ALTER'
        elif query_upper.startswith('DROP'):
            return 'DROP'
        else:
            return 'OTHER'
    
    def _detect_business_domain(self, table_name: str, columns: List[ColumnInfo]) -> str:
        """
        Detect business domain from table name and columns.
        
        Args:
            table_name: Name of the table
            columns: List of column information
            
        Returns:
            str: Detected business domain
        """
        table_lower = table_name.lower()
        column_names = [col.name.lower() for col in columns]
        
        # Financial domain
        if any(keyword in table_lower for keyword in ['account', 'transaction', 'payment', 'invoice', 'financial']):
            return 'finance'
        
        # CRM domain
        if any(keyword in table_lower for keyword in ['customer', 'contact', 'lead', 'opportunity', 'client']):
            return 'crm'
        
        # E-commerce domain
        if any(keyword in table_lower for keyword in ['product', 'order', 'cart', 'inventory', 'shipping']):
            return 'ecommerce'
        
        # Procurement domain
        if any(keyword in table_lower for keyword in ['purchase', 'vendor', 'supplier', 'procurement', 'requisition']):
            return 'procurement'
        
        # HR domain
        if any(keyword in table_lower for keyword in ['employee', 'hr', 'payroll', 'attendance', 'department']):
            return 'hr'
        
        # Healthcare domain
        if any(keyword in table_lower for keyword in ['patient', 'medical', 'health', 'diagnosis', 'treatment']):
            return 'healthcare'
        
        # Manufacturing domain
        if any(keyword in table_lower for keyword in ['production', 'manufacturing', 'quality', 'assembly', 'workorder']):
            return 'manufacturing'
        
        return 'general'
    
    def _extract_plan_cost(self, plan_xml: str) -> Optional[float]:
        """
        Extract cost from execution plan XML.
        
        Args:
            plan_xml: Execution plan XML string
            
        Returns:
            Optional[float]: Estimated cost
        """
        try:
            import re
            cost_match = re.search(r'EstimatedTotalSubtreeCost="([^"]+)"', plan_xml)
            if cost_match:
                return float(cost_match.group(1))
        except Exception:
            pass
        return None
    
    def _extract_plan_rows(self, plan_xml: str) -> Optional[int]:
        """
        Extract estimated rows from execution plan XML.
        
        Args:
            plan_xml: Execution plan XML string
            
        Returns:
            Optional[int]: Estimated number of rows
        """
        try:
            import re
            rows_match = re.search(r'EstimatedRows="([^"]+)"', plan_xml)
            if rows_match:
                return int(float(rows_match.group(1)))
        except Exception:
            pass
        return None


class SQLServerConnectionPool:
    """
    Simple connection pool for SQL Server.
    """
    
    def __init__(self, connection_string: str, pool_size: int = 10, 
                 max_overflow: int = 20, timeout: int = 30):
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.timeout = timeout
        self._pool = asyncio.Queue(maxsize=pool_size + max_overflow)
        self._created_connections = 0
        self._lock = asyncio.Lock()
    
    async def get_connection(self):
        """
        Get connection from pool.
        
        Returns:
            pyodbc.Connection: Database connection
        """
        try:
            # Try to get existing connection
            connection = self._pool.get_nowait()
            return connection
        except asyncio.QueueEmpty:
            # Create new connection
            async with self._lock:
                if self._created_connections < self.pool_size + self.max_overflow:
                    connection = pyodbc.connect(
                        self.connection_string, 
                        timeout=self.timeout
                    )
                    self._created_connections += 1
                    return connection
                else:
                    # Wait for connection to become available
                    connection = await asyncio.wait_for(
                        self._pool.get(), 
                        timeout=self.timeout
                    )
                    return connection
    
    async def return_connection(self, connection):
        """
        Return connection to pool.
        
        Args:
            connection: Database connection to return
        """
        try:
            self._pool.put_nowait(connection)
        except asyncio.QueueFull:
            # Pool is full, close connection
            connection.close()
            async with self._lock:
                if self._created_connections > 0:
                    self._created_connections -= 1
    
    def close(self):
        """
        Close all connections in pool.
        """
        while not self._pool.empty():
            try:
                connection = self._pool.get_nowait()
                connection.close()
            except asyncio.QueueEmpty:
                break
        self._created_connections = 0
