# Database Adapter Framework

A universal database connectivity framework that provides a consistent interface for connecting to and interacting with different database systems.

## 🎯 **Overview**

The Database Adapter Framework is the foundation of the Global RAG Platform, enabling universal connectivity to any database system while maintaining consistent interfaces and functionality across different database engines.

## 🏗️ **Architecture**

### **Core Components**

1. **`DatabaseAdapter`** - Abstract base class defining the common interface
2. **`DatabaseType`** - Enumeration of supported database types
3. **`ConnectionConfig`** - Configuration for database connections
4. **`QueryResult`** - Standardized query result format
5. **`DatabaseSchema`** - Database schema information
6. **`TableInfo`** - Table metadata and structure
7. **`ColumnInfo`** - Column metadata and properties

### **Supported Database Types**

- **PostgreSQL** - Full support with asyncpg
- **SQL Server** - Full support with pyodbc
- **MySQL** - Full support with aiomysql
- **Oracle** - Full support with cx-Oracle
- **MongoDB** - Full support with motor
- **SQLite** - Full support with aiosqlite

## 🚀 **Quick Start**

### **Installation**

```bash
pip install -r requirements.txt
```

### **Basic Usage**

```python
import asyncio
from adapters.database_adapter import DatabaseAdapter, ConnectionConfig, DatabaseType

# Create connection configuration
config = ConnectionConfig(
    host="localhost",
    port=5432,
    database="my_database",
    username="my_user",
    password="my_password"
)

# Create adapter instance (replace with specific adapter)
adapter = PostgreSQLAdapter(config)

# Use context manager for automatic connection handling
async with adapter:
    # Execute queries
    result = await adapter.execute_query("SELECT * FROM users LIMIT 10")
    print(f"Found {result.row_count} users")
    
    # Get schema information
    schema = await adapter.get_schema()
    print(f"Database has {len(schema.tables)} tables")
    
    # Get table information
    users_table = await adapter.get_table_info("users")
    print(f"Users table has {len(users_table.columns)} columns")
```

## 📚 **API Reference**

### **DatabaseAdapter**

The abstract base class that all database adapters must implement.

#### **Core Methods**

- `connect()` - Establish database connection
- `disconnect()` - Close database connection
- `execute_query(query, params)` - Execute a single query
- `execute_batch(queries)` - Execute multiple queries
- `get_schema(force_refresh)` - Get database schema
- `get_table_info(table_name, schema)` - Get table information
- `get_table_data(table_name, limit, offset, schema)` - Get sample data
- `validate_query(query)` - Validate query syntax
- `get_query_plan(query)` - Get query execution plan
- `test_connection()` - Test database connectivity

#### **Utility Methods**

- `get_table_names()` - Get all table names
- `get_column_names(table_name, schema)` - Get column names
- `get_table_row_count(table_name, schema)` - Get row count
- `get_table_size(table_name, schema)` - Get table size
- `get_database_size()` - Get total database size
- `get_database_version()` - Get database version

### **ConnectionConfig**

Configuration class for database connections.

```python
@dataclass
class ConnectionConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_mode: Optional[str] = None
    connection_timeout: int = 30
    pool_size: int = 10
    max_overflow: int = 20
```

### **QueryResult**

Standardized format for query results.

```python
@dataclass
class QueryResult:
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time: float
    query_id: str
    timestamp: datetime
    metadata: Dict[str, Any]
```

### **DatabaseSchema**

Complete database schema information.

```python
@dataclass
class DatabaseSchema:
    database_name: str
    tables: List[TableInfo]
    views: List[ViewInfo]
    functions: List[FunctionInfo]
    procedures: List[ProcedureInfo]
    total_size_bytes: int
    version: str
    description: str
```

## 🔧 **Configuration**

### **Environment Variables**

```bash
# Database connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=my_database
DB_USER=my_user
DB_PASSWORD=my_password

# Connection pool settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_CONNECTION_TIMEOUT=30

# SSL settings
DB_SSL_MODE=require
```

### **Configuration File**

```yaml
# config/database.yaml
databases:
  postgresql:
    host: localhost
    port: 5432
    database: my_database
    username: my_user
    password: my_password
    ssl_mode: require
    pool_size: 10
    max_overflow: 20
    connection_timeout: 30
  
  sqlserver:
    host: sqlserver.example.com
    port: 1433
    database: my_database
    username: my_user
    password: my_password
    ssl_mode: require
    pool_size: 5
    max_overflow: 10
    connection_timeout: 30
```

## 🧪 **Testing**

### **Run Tests**

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_database_adapter.py -v

# Run with coverage
python -m pytest tests/ --cov=adapters --cov-report=html
```

### **Test Structure**

```
tests/
├── test_database_adapter.py      # Core adapter tests
├── test_postgresql_adapter.py    # PostgreSQL-specific tests
├── test_sqlserver_adapter.py     # SQL Server-specific tests
├── test_mysql_adapter.py         # MySQL-specific tests
├── test_oracle_adapter.py        # Oracle-specific tests
├── test_mongodb_adapter.py       # MongoDB-specific tests
└── test_sqlite_adapter.py        # SQLite-specific tests
```

## 📖 **Examples**

### **Example 1: Basic Query Execution**

```python
import asyncio
from adapters.database_adapter import PostgreSQLAdapter, ConnectionConfig

async def basic_query_example():
    config = ConnectionConfig(
        host="localhost",
        port=5432,
        database="ecommerce",
        username="postgres",
        password="password"
    )
    
    async with PostgreSQLAdapter(config) as adapter:
        # Execute a simple query
        result = await adapter.execute_query("SELECT * FROM users LIMIT 5")
        
        print(f"Query returned {result.row_count} rows")
        for row in result.data:
            print(f"User: {row['name']} ({row['email']})")
```

### **Example 2: Schema Introspection**

```python
async def schema_introspection_example():
    config = ConnectionConfig(
        host="localhost",
        port=5432,
        database="ecommerce",
        username="postgres",
        password="password"
    )
    
    async with PostgreSQLAdapter(config) as adapter:
        # Get complete database schema
        schema = await adapter.get_schema()
        
        print(f"Database: {schema.database_name}")
        print(f"Version: {schema.version}")
        print(f"Total size: {schema.total_size_bytes} bytes")
        
        # Analyze each table
        for table in schema.tables:
            print(f"\nTable: {table.name}")
            print(f"  Domain: {table.business_domain}")
            print(f"  Rows: {table.row_count}")
            print(f"  Size: {table.size_bytes} bytes")
            print(f"  Columns: {len(table.columns)}")
            
            for column in table.columns:
                pk_marker = " (PK)" if column.is_primary_key else ""
                fk_marker = " (FK)" if column.is_foreign_key else ""
                print(f"    - {column.name}: {column.data_type}{pk_marker}{fk_marker}")
```

### **Example 3: Batch Operations**

```python
async def batch_operations_example():
    config = ConnectionConfig(
        host="localhost",
        port=5432,
        database="ecommerce",
        username="postgres",
        password="password"
    )
    
    async with PostgreSQLAdapter(config) as adapter:
        # Execute multiple queries in batch
        queries = [
            "SELECT COUNT(*) as user_count FROM users",
            "SELECT COUNT(*) as order_count FROM orders",
            "SELECT COUNT(*) as product_count FROM products"
        ]
        
        results = await adapter.execute_batch(queries)
        
        for i, result in enumerate(results):
            count = result.data[0][f"{queries[i].split('FROM ')[1].split(' ')[0]}_count"]
            print(f"{queries[i].split('FROM ')[1].split(' ')[0].title()}: {count}")
```

### **Example 4: Error Handling**

```python
async def error_handling_example():
    config = ConnectionConfig(
        host="localhost",
        port=5432,
        database="ecommerce",
        username="postgres",
        password="password"
    )
    
    adapter = PostgreSQLAdapter(config)
    
    try:
        # Try to execute query without connection
        await adapter.execute_query("SELECT * FROM users")
    except ConnectionError as e:
        print(f"Connection error: {e}")
    
    try:
        # Connect and try invalid query
        await adapter.connect()
        await adapter.execute_query("INVALID SQL STATEMENT")
    except QueryError as e:
        print(f"Query error: {e}")
    except SchemaError as e:
        print(f"Schema error: {e}")
    finally:
        await adapter.disconnect()
```

## 🔒 **Security**

### **Connection Security**

- **SSL/TLS Encryption** - All connections support SSL/TLS encryption
- **Connection Pooling** - Secure connection pooling with configurable limits
- **Timeout Management** - Configurable connection and query timeouts
- **Credential Management** - Secure credential handling and validation

### **Query Security**

- **SQL Injection Prevention** - Parameterized queries prevent SQL injection
- **Query Validation** - Built-in query syntax validation
- **Access Control** - Database-level access control integration
- **Audit Logging** - Comprehensive query and connection logging

## 📊 **Performance**

### **Connection Pooling**

- **Configurable Pool Size** - Adjust pool size based on workload
- **Overflow Handling** - Handle connection overflow gracefully
- **Connection Reuse** - Efficient connection reuse and management
- **Health Monitoring** - Monitor connection health and performance

### **Query Optimization**

- **Query Planning** - Get execution plans for optimization
- **Batch Operations** - Execute multiple queries efficiently
- **Async Operations** - Non-blocking async operations
- **Result Streaming** - Stream large result sets efficiently

## 🚀 **Next Steps**

1. **Implement Specific Adapters** - Create concrete implementations for each database type
2. **Add Connection Manager** - Implement centralized connection management
3. **Schema Introspector** - Build dynamic schema discovery and mapping
4. **Query Optimizer** - Add query optimization and caching
5. **Monitoring** - Implement comprehensive monitoring and metrics

## 📝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 **Support**

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the examples
- Run the test suite
