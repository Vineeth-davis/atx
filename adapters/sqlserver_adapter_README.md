# SQL Server Database Adapter

A production-ready adapter for Microsoft SQL Server that provides full support for SQL Server-specific features, connection pooling, schema introspection, and enterprise-grade functionality.

## 🎯 **Overview**

The SQL Server Adapter is a concrete implementation of the Database Adapter Framework, specifically designed for Microsoft SQL Server databases. It provides comprehensive support for SQL Server features including stored procedures, functions, triggers, indexes, and advanced data types.

## 🏗️ **Features**

### **Core Features**
- **Full SQL Server Support** - Compatible with SQL Server 2016 and later
- **Connection Pooling** - Efficient connection management with configurable pool sizes
- **Schema Introspection** - Complete database schema discovery and mapping
- **Query Execution** - Parameterized queries with comprehensive error handling
- **Transaction Support** - Full transaction management capabilities
- **Performance Optimization** - Query planning and execution optimization

### **SQL Server Specific Features**
- **Authentication Methods** - Windows Authentication and SQL Server Authentication
- **SSL/TLS Encryption** - Secure connections with configurable encryption levels
- **Advanced Data Types** - Support for all SQL Server data types including XML, JSON, and spatial data
- **Stored Procedures & Functions** - Discovery and execution of SQL Server routines
- **Index Management** - Clustered and non-clustered index information
- **Foreign Key Relationships** - Complete relationship mapping with constraint details
- **Business Domain Detection** - Automatic detection of business domains from schema

### **Enterprise Features**
- **Connection String Management** - Flexible connection string building
- **Driver Support** - Multiple ODBC driver support (17, 18, 19)
- **Timeout Management** - Configurable connection and query timeouts
- **Error Handling** - Comprehensive error handling with detailed error messages
- **Logging** - Structured logging for debugging and monitoring
- **Context Manager** - Python context manager support for automatic connection handling

## 🚀 **Quick Start**

### **Installation**

```bash
pip install pyodbc
```

### **Basic Usage**

```python
import asyncio
from adapters.sqlserver_adapter import SQLServerAdapter
from adapters.database_adapter import ConnectionConfig

# Create connection configuration
config = ConnectionConfig(
    host="sqlserver.company.com",
    port=1433,
    database="puma_procurement",
    username="puma_user",
    password="secure_password",
    driver="ODBC Driver 17 for SQL Server",
    ssl_mode="require",
    connection_timeout=30,
    pool_size=10,
    max_overflow=20
)

# Use context manager for automatic connection handling
async with SQLServerAdapter(config) as adapter:
    # Execute queries
    result = await adapter.execute_query("SELECT * FROM vendors WHERE active = 1")
    print(f"Found {result.row_count} active vendors")
    
    # Get schema information
    schema = await adapter.get_schema()
    print(f"Database has {len(schema.tables)} tables")
    
    # Get table information
    vendors_table = await adapter.get_table_info("vendors")
    print(f"Vendors table has {len(vendors_table.columns)} columns")
```

## 📚 **API Reference**

### **SQLServerAdapter**

The main adapter class for SQL Server connectivity.

#### **Constructor**

```python
SQLServerAdapter(config: ConnectionConfig)
```

**Parameters:**
- `config`: Database connection configuration

#### **Core Methods**

- `connect()` - Establish connection to SQL Server
- `disconnect()` - Close connection and cleanup resources
- `execute_query(query, params)` - Execute SQL query with optional parameters
- `execute_batch(queries)` - Execute multiple queries in batch
- `get_schema(force_refresh)` - Get complete database schema
- `get_table_info(table_name, schema)` - Get detailed table information
- `get_table_data(table_name, limit, offset, schema)` - Get sample data from table
- `validate_query(query)` - Validate SQL query syntax
- `get_query_plan(query)` - Get query execution plan
- `test_connection()` - Test database connectivity

#### **Utility Methods**

- `get_table_names(schema)` - Get list of table names
- `get_column_names(table_name, schema)` - Get column names for table
- `get_table_size(table_name, schema)` - Get table size in bytes
- `get_table_row_count(table_name, schema)` - Get number of rows in table

### **ConnectionConfig**

Configuration class for SQL Server connections.

```python
@dataclass
class ConnectionConfig:
    host: str                    # SQL Server hostname or IP
    port: int                   # SQL Server port (default: 1433)
    database: str               # Database name
    username: str               # Username (empty for Windows Auth)
    password: str               # Password (empty for Windows Auth)
    driver: Optional[str]       # ODBC driver name
    ssl_mode: Optional[str]    # SSL mode: require, prefer, disable
    connection_timeout: int     # Connection timeout in seconds
    pool_size: int             # Connection pool size
    max_overflow: int          # Maximum overflow connections
```

## 🔧 **Configuration**

### **Connection String Options**

The adapter automatically builds connection strings based on configuration:

#### **SQL Server Authentication**
```
DRIVER={ODBC Driver 17 for SQL Server};
SERVER=hostname,port;
DATABASE=database_name;
UID=username;
PWD=password;
Connection Timeout=30;
```

#### **Windows Authentication**
```
DRIVER={ODBC Driver 17 for SQL Server};
SERVER=hostname,port;
DATABASE=database_name;
Trusted_Connection=yes;
Connection Timeout=30;
```

#### **SSL/TLS Encryption**
```
Encrypt=yes;TrustServerCertificate=no;  # require
Encrypt=optional;TrustServerCertificate=yes;  # prefer
Encrypt=no;  # disable
```

### **Environment Variables**

```bash
# SQL Server connection
SQLSERVER_HOST=sqlserver.company.com
SQLSERVER_PORT=1433
SQLSERVER_DATABASE=puma_procurement
SQLSERVER_USERNAME=puma_user
SQLSERVER_PASSWORD=secure_password

# Connection settings
SQLSERVER_DRIVER=ODBC Driver 17 for SQL Server
SQLSERVER_SSL_MODE=require
SQLSERVER_CONNECTION_TIMEOUT=30
SQLSERVER_POOL_SIZE=10
SQLSERVER_MAX_OVERFLOW=20
```

### **Configuration File**

```yaml
# config/sqlserver.yaml
sqlserver:
  host: sqlserver.company.com
  port: 1433
  database: puma_procurement
  username: puma_user
  password: secure_password
  driver: "ODBC Driver 17 for SQL Server"
  ssl_mode: require
  connection_timeout: 30
  pool_size: 10
  max_overflow: 20
```

## 🧪 **Testing**

### **Run Tests**

```bash
# Run SQL Server adapter tests
python -m pytest tests/test_sqlserver_adapter.py -v

# Run with coverage
python -m pytest tests/test_sqlserver_adapter.py --cov=adapters.sqlserver_adapter --cov-report=html
```

### **Test Structure**

```
tests/
├── test_sqlserver_adapter.py      # SQL Server adapter tests
│   ├── TestSQLServerAdapter       # Main adapter tests
│   └── TestSQLServerConnectionPool # Connection pool tests
```

## 📖 **Examples**

### **Example 1: Basic Query Execution**

```python
import asyncio
from adapters.sqlserver_adapter import SQLServerAdapter
from adapters.database_adapter import ConnectionConfig

async def basic_query_example():
    config = ConnectionConfig(
        host="sqlserver.company.com",
        port=1433,
        database="puma_procurement",
        username="puma_user",
        password="secure_password"
    )
    
    async with SQLServerAdapter(config) as adapter:
        # Execute a simple query
        result = await adapter.execute_query("SELECT * FROM vendors LIMIT 10")
        
        print(f"Query returned {result.row_count} rows")
        for row in result.data:
            print(f"Vendor: {row['vendor_name']} ({row['contact_email']})")
```

### **Example 2: Schema Introspection**

```python
async def schema_introspection_example():
    config = ConnectionConfig(
        host="sqlserver.company.com",
        port=1433,
        database="puma_procurement",
        username="puma_user",
        password="secure_password"
    )
    
    async with SQLServerAdapter(config) as adapter:
        # Get complete database schema
        schema = await adapter.get_schema()
        
        print(f"Database: {schema.database_name}")
        print(f"Version: {schema.version}")
        print(f"Total size: {schema.total_size_bytes:,} bytes")
        
        # Analyze each table
        for table in schema.tables:
            print(f"\nTable: {table.schema}.{table.name}")
            print(f"  Domain: {table.business_domain}")
            print(f"  Rows: {table.row_count:,}")
            print(f"  Size: {table.size_bytes:,} bytes")
            print(f"  Columns: {len(table.columns)}")
            
            for column in table.columns:
                pk_marker = " (PK)" if column.is_primary_key else ""
                fk_marker = " (FK)" if column.is_foreign_key else ""
                print(f"    - {column.name}: {column.data_type}{pk_marker}{fk_marker}")
```

### **Example 3: Parameterized Queries**

```python
async def parameterized_query_example():
    config = ConnectionConfig(
        host="sqlserver.company.com",
        port=1433,
        database="puma_procurement",
        username="puma_user",
        password="secure_password"
    )
    
    async with SQLServerAdapter(config) as adapter:
        # Execute parameterized query
        params = {
            'vendor_id': 123,
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }
        
        query = """
        SELECT po.po_id, po.order_date, po.total_amount, v.vendor_name
        FROM purchase_orders po
        JOIN vendors v ON po.vendor_id = v.vendor_id
        WHERE po.vendor_id = ? 
        AND po.order_date BETWEEN ? AND ?
        ORDER BY po.order_date DESC
        """
        
        result = await adapter.execute_query(query, params)
        
        print(f"Found {result.row_count} purchase orders")
        for row in result.data:
            print(f"PO {row['po_id']}: {row['vendor_name']} - ${row['total_amount']:,.2f}")
```

### **Example 4: Batch Operations**

```python
async def batch_operations_example():
    config = ConnectionConfig(
        host="sqlserver.company.com",
        port=1433,
        database="puma_procurement",
        username="puma_user",
        password="secure_password"
    )
    
    async with SQLServerAdapter(config) as adapter:
        # Execute multiple queries in batch
        queries = [
            "SELECT COUNT(*) as vendor_count FROM vendors",
            "SELECT COUNT(*) as po_count FROM purchase_orders",
            "SELECT COUNT(*) as category_count FROM categories",
            "SELECT SUM(total_amount) as total_spent FROM purchase_orders"
        ]
        
        results = await adapter.execute_batch(queries)
        
        metrics = {
            'vendors': results[0].data[0]['vendor_count'],
            'purchase_orders': results[1].data[0]['po_count'],
            'categories': results[2].data[0]['category_count'],
            'total_spent': results[3].data[0]['total_spent']
        }
        
        print("Procurement Metrics:")
        for key, value in metrics.items():
            print(f"  {key.replace('_', ' ').title()}: {value:,}")
```

### **Example 5: Error Handling**

```python
async def error_handling_example():
    config = ConnectionConfig(
        host="sqlserver.company.com",
        port=1433,
        database="puma_procurement",
        username="puma_user",
        password="secure_password"
    )
    
    adapter = SQLServerAdapter(config)
    
    try:
        # Try to execute query without connection
        await adapter.execute_query("SELECT * FROM vendors")
    except Exception as e:
        print(f"Connection error: {e}")
    
    try:
        # Connect and try invalid query
        await adapter.connect()
        await adapter.execute_query("INVALID SQL STATEMENT")
    except Exception as e:
        print(f"Query error: {e}")
    finally:
        await adapter.disconnect()
```

## 🔒 **Security**

### **Connection Security**

- **SSL/TLS Encryption** - All connections support SSL/TLS encryption
- **Windows Authentication** - Support for Windows Authentication (Trusted Connection)
- **SQL Server Authentication** - Username/password authentication
- **Connection Pooling** - Secure connection pooling with configurable limits
- **Timeout Management** - Configurable connection and query timeouts

### **Query Security**

- **SQL Injection Prevention** - Parameterized queries prevent SQL injection
- **Query Validation** - Built-in query syntax validation using SQL Server's PARSEONLY
- **Access Control** - Database-level access control integration
- **Audit Logging** - Comprehensive query and connection logging

## 📊 **Performance**

### **Connection Pooling**

- **Configurable Pool Size** - Adjust pool size based on workload (default: 10)
- **Overflow Handling** - Handle connection overflow gracefully (default: 20)
- **Connection Reuse** - Efficient connection reuse and management
- **Health Monitoring** - Monitor connection health and performance

### **Query Optimization**

- **Query Planning** - Get execution plans for optimization
- **Batch Operations** - Execute multiple queries efficiently
- **Async Operations** - Non-blocking async operations
- **Result Streaming** - Stream large result sets efficiently

## 🚀 **SQL Server Specific Features**

### **Data Types**

- **Numeric**: int, bigint, smallint, tinyint, decimal, numeric, money, smallmoney, float, real
- **String**: varchar, nvarchar, char, nchar, text, ntext
- **Date/Time**: datetime, datetime2, date, time, smalldatetime
- **Binary**: binary, varbinary, image
- **Other**: bit, uniqueidentifier, xml, json, sql_variant, hierarchyid, geometry, geography

### **Advanced Features**

- **Stored Procedures** - Discovery and execution of stored procedures
- **Functions** - User-defined function support
- **Triggers** - Trigger information and management
- **Indexes** - Clustered and non-clustered index support
- **Views** - View discovery and information
- **Constraints** - Primary key, foreign key, check, and unique constraints
- **Extended Properties** - MS_Description and custom properties

### **Business Domain Detection**

The adapter automatically detects business domains from table and column names:

- **Finance**: account, transaction, payment, invoice, financial
- **CRM**: customer, contact, lead, opportunity, client
- **E-commerce**: product, order, cart, inventory, shipping
- **Procurement**: purchase, vendor, supplier, procurement, requisition
- **HR**: employee, hr, payroll, attendance, department
- **Healthcare**: patient, medical, health, diagnosis, treatment
- **Manufacturing**: production, manufacturing, quality, assembly, workorder

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Connection Issues**
```
Error: [Microsoft][ODBC Driver 17 for SQL Server]TCP Provider: No connection could be made
```
**Solution**: Check hostname, port, and network connectivity

#### **Authentication Issues**
```
Error: Login failed for user 'username'
```
**Solution**: Verify username/password or enable Windows Authentication

#### **Driver Issues**
```
Error: [Microsoft][ODBC Driver Manager] Data source name not found
```
**Solution**: Install correct ODBC driver or update driver name

#### **SSL Issues**
```
Error: SSL Provider: No credentials are available
```
**Solution**: Configure SSL settings or use TrustServerCertificate=yes

### **Debugging**

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# SQL Server adapter will now log detailed information
```

### **Performance Issues**

- **Slow Queries**: Use `get_query_plan()` to analyze execution plans
- **Connection Timeouts**: Increase `connection_timeout` setting
- **Pool Exhaustion**: Increase `pool_size` and `max_overflow`
- **Memory Usage**: Monitor connection pool usage

## 📈 **Monitoring**

### **Metrics to Monitor**

- **Connection Pool Usage**: Active vs. available connections
- **Query Performance**: Execution times and row counts
- **Error Rates**: Connection and query error frequencies
- **Resource Usage**: Memory and CPU utilization

### **Logging**

The adapter provides structured logging for:

- Connection events (connect, disconnect, errors)
- Query execution (query text, execution time, row count)
- Schema operations (schema refresh, table discovery)
- Performance metrics (pool usage, query plans)

## 🚀 **Next Steps**

1. **Implement PostgreSQL Adapter** - Create concrete PostgreSQL adapter
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
