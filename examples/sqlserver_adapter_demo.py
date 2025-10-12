"""
SQL Server Adapter Demonstration

This example demonstrates how to use the SQL Server adapter
for connecting to Microsoft SQL Server databases.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from adapters.sqlserver_adapter import SQLServerAdapter
from adapters.database_adapter import (
    ConnectionConfig,
    DatabaseType,
    QueryResult,
    ColumnInfo,
    TableInfo,
    DatabaseSchema,
    QueryPlan,
    ForeignKeyInfo,
    IndexInfo,
    SchemaError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockSQLServerAdapter(SQLServerAdapter):
    """
    Mock implementation of SQL Server adapter for demonstration purposes.
    This shows how to use the adapter interface with simulated data.
    """
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self._mock_data = {
            "dbo.users": [
                {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30, "department_id": 1},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25, "department_id": 2},
                {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "age": 35, "department_id": 1}
            ],
            "dbo.departments": [
                {"id": 1, "name": "Engineering", "budget": 1000000.00, "manager_id": 1},
                {"id": 2, "name": "Marketing", "budget": 500000.00, "manager_id": 2}
            ],
            "dbo.orders": [
                {"id": 1, "user_id": 1, "product": "Laptop", "amount": 999.99, "order_date": "2024-01-15"},
                {"id": 2, "user_id": 2, "product": "Mouse", "amount": 29.99, "order_date": "2024-01-16"},
                {"id": 3, "user_id": 1, "product": "Keyboard", "amount": 79.99, "order_date": "2024-01-17"}
            ]
        }
    
    async def connect(self) -> bool:
        """Simulate SQL Server connection."""
        logger.info(f"Connecting to SQL Server: {self.config.host}:{self.config.port}/{self.config.database}")
        self.is_connected = True
        return True
    
    async def disconnect(self) -> bool:
        """Simulate SQL Server disconnection."""
        logger.info("Disconnecting from SQL Server")
        self.is_connected = False
        return True
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> QueryResult:
        """Simulate query execution with mock data."""
        if not self.is_connected:
            raise Exception("Not connected to database")
        
        logger.info(f"Executing SQL Server query: {query}")
        
        # Simple query parsing for demonstration
        query_lower = query.lower().strip()
        
        if "select * from users" in query_lower:
            data = self._mock_data["dbo.users"]
            columns = ["id", "name", "email", "age", "department_id"]
        elif "select * from departments" in query_lower:
            data = self._mock_data["dbo.departments"]
            columns = ["id", "name", "budget", "manager_id"]
        elif "select * from orders" in query_lower:
            data = self._mock_data["dbo.orders"]
            columns = ["id", "user_id", "product", "amount", "order_date"]
        elif "select count(*) from users" in query_lower:
            data = [{"count": len(self._mock_data["dbo.users"])}]
            columns = ["count"]
        elif "select @@version" in query_lower:
            data = [{"version": "Microsoft SQL Server 2019 (RTM-CU18) (KB5017593) - 15.0.4261.1 (X64)"}]
            columns = ["version"]
        else:
            data = []
            columns = []
        
        return QueryResult(
            data=data,
            columns=columns,
            row_count=len(data),
            execution_time=0.001,
            query_id=self._generate_query_id(),
            timestamp=datetime.utcnow(),
            metadata={"database": "sqlserver", "query_type": "select", "server": f"{self.config.host}:{self.config.port}"}
        )
    
    async def get_schema(self, force_refresh: bool = False) -> DatabaseSchema:
        """Get mock SQL Server schema."""
        tables = [
            TableInfo(
                name="users",
                schema="dbo",
                columns=[
                    ColumnInfo(name="id", data_type="int", is_nullable=False, is_primary_key=True, is_foreign_key=False),
                    ColumnInfo(name="name", data_type="varchar", is_nullable=False, max_length=100),
                    ColumnInfo(name="email", data_type="varchar", is_nullable=False, max_length=255, is_unique=True),
                    ColumnInfo(name="age", data_type="int", is_nullable=True),
                    ColumnInfo(name="department_id", data_type="int", is_nullable=False, is_foreign_key=True)
                ],
                primary_keys=["id"],
                foreign_keys=[
                    ForeignKeyInfo(
                        column_name="department_id",
                        referenced_table="departments",
                        referenced_column="id",
                        constraint_name="FK_users_departments"
                    )
                ],
                indexes=[
                    IndexInfo(name="PK_users", columns=["id"], is_primary=True, is_clustered=True),
                    IndexInfo(name="IX_users_email", columns=["email"], is_unique=True)
                ],
                row_count=len(self._mock_data["dbo.users"]),
                size_bytes=2048,
                description="User information table",
                business_domain="crm"
            ),
            TableInfo(
                name="departments",
                schema="dbo",
                columns=[
                    ColumnInfo(name="id", data_type="int", is_nullable=False, is_primary_key=True),
                    ColumnInfo(name="name", data_type="varchar", is_nullable=False, max_length=100),
                    ColumnInfo(name="budget", data_type="decimal", is_nullable=False, precision=10, scale=2),
                    ColumnInfo(name="manager_id", data_type="int", is_nullable=True, is_foreign_key=True)
                ],
                primary_keys=["id"],
                foreign_keys=[],
                indexes=[
                    IndexInfo(name="PK_departments", columns=["id"], is_primary=True, is_clustered=True)
                ],
                row_count=len(self._mock_data["dbo.departments"]),
                size_bytes=1024,
                description="Department information table",
                business_domain="hr"
            ),
            TableInfo(
                name="orders",
                schema="dbo",
                columns=[
                    ColumnInfo(name="id", data_type="int", is_nullable=False, is_primary_key=True),
                    ColumnInfo(name="user_id", data_type="int", is_nullable=False, is_foreign_key=True),
                    ColumnInfo(name="product", data_type="varchar", is_nullable=False, max_length=100),
                    ColumnInfo(name="amount", data_type="decimal", is_nullable=False, precision=10, scale=2),
                    ColumnInfo(name="order_date", data_type="date", is_nullable=False)
                ],
                primary_keys=["id"],
                foreign_keys=[
                    ForeignKeyInfo(
                        column_name="user_id",
                        referenced_table="users",
                        referenced_column="id",
                        constraint_name="FK_orders_users"
                    )
                ],
                indexes=[
                    IndexInfo(name="PK_orders", columns=["id"], is_primary=True, is_clustered=True),
                    IndexInfo(name="IX_orders_user_id", columns=["user_id"])
                ],
                row_count=len(self._mock_data["dbo.orders"]),
                size_bytes=1536,
                description="Order information table",
                business_domain="ecommerce"
            )
        ]
        
        return DatabaseSchema(
            database_name=self.config.database,
            tables=tables,
            views=[],
            functions=["dbo.GetUserCount", "dbo.CalculateTotalSales"],
            procedures=["dbo.CreateUser", "dbo.UpdateUser", "dbo.DeleteUser"],
            total_size_bytes=4608,
            version="Microsoft SQL Server 2019",
            description="SQL Server database for demonstration"
        )
    
    async def get_table_info(self, table_name: str, schema: Optional[str] = None) -> TableInfo:
        """Get information about a specific table."""
        schema_info = await self.get_schema()
        for table in schema_info.tables:
            if table.name == table_name and table.schema == (schema or "dbo"):
                return table
        raise SchemaError(f"Table {schema or 'dbo'}.{table_name} not found")
    
    async def validate_query(self, query: str) -> bool:
        """Validate query syntax."""
        query_lower = query.lower().strip()
        return query_lower.startswith(('select', 'insert', 'update', 'delete', 'create', 'alter', 'drop'))
    
    async def get_query_plan(self, query: str) -> QueryPlan:
        """Get mock query execution plan."""
        return QueryPlan(
            plan_type="SQL Server Execution Plan",
            cost=1.0,
            rows_estimated=100,
            execution_time=0.001,
            details={"type": "mock", "table": "users", "database": "sqlserver"}
        )
    
    async def test_connection(self) -> bool:
        """Test database connectivity."""
        return self.is_connected
    
    async def _get_version(self) -> str:
        """Get database version."""
        return "Microsoft SQL Server 2019"


async def demonstrate_sqlserver_adapter():
    """Demonstrate the SQL Server adapter functionality."""
    
    print("🚀 SQL Server Adapter Demonstration")
    print("=" * 50)
    
    # Create connection configuration
    config = ConnectionConfig(
        host="sqlserver.example.com",
        port=1433,
        database="puma_procurement",
        username="puma_user",
        password="puma_password",
        driver="ODBC Driver 17 for SQL Server",
        ssl_mode="require",
        connection_timeout=30,
        pool_size=10,
        max_overflow=20
    )
    
    # Create adapter instance
    adapter = MockSQLServerAdapter(config)
    
    try:
        # Demonstrate connection
        print("\n📡 Connecting to SQL Server...")
        await adapter.connect()
        print(f"✅ Connected to {adapter.database_type.value} database")
        print(f"✅ Server: {config.host}:{config.port}")
        print(f"✅ Database: {config.database}")
        print(f"✅ Driver: {config.driver}")
        
        # Demonstrate schema retrieval
        print("\n📊 Retrieving SQL Server schema...")
        schema = await adapter.get_schema()
        print(f"✅ Database: {schema.database_name}")
        print(f"✅ Version: {schema.version}")
        print(f"✅ Tables: {len(schema.tables)}")
        print(f"✅ Functions: {len(schema.functions)}")
        print(f"✅ Procedures: {len(schema.procedures)}")
        print(f"✅ Total size: {schema.total_size_bytes:,} bytes")
        
        for table in schema.tables:
            print(f"   📋 {table.schema}.{table.name} ({table.business_domain}) - {table.row_count} rows")
            print(f"      🔑 Primary keys: {', '.join(table.primary_keys)}")
            print(f"      🔗 Foreign keys: {len(table.foreign_keys)}")
            print(f"      📊 Indexes: {len(table.indexes)}")
        
        # Demonstrate query execution
        print("\n🔍 Executing SQL Server queries...")
        
        # Query 1: Get all users
        result1 = await adapter.execute_query("SELECT * FROM users")
        print(f"✅ Query 1: Found {result1.row_count} users")
        for row in result1.data[:2]:  # Show first 2 rows
            print(f"   👤 {row['name']} ({row['email']}) - Age: {row['age']}")
        
        # Query 2: Get departments
        result2 = await adapter.execute_query("SELECT * FROM departments")
        print(f"✅ Query 2: Found {result2.row_count} departments")
        for row in result2.data:
            print(f"   🏢 {row['name']} - Budget: ${row['budget']:,.2f}")
        
        # Query 3: Get orders
        result3 = await adapter.execute_query("SELECT * FROM orders")
        print(f"✅ Query 3: Found {result3.row_count} orders")
        for row in result3.data[:2]:  # Show first 2 rows
            print(f"   🛒 Order {row['id']}: {row['product']} - ${row['amount']}")
        
        # Query 4: Count users
        result4 = await adapter.execute_query("SELECT COUNT(*) FROM users")
        print(f"✅ Query 4: Total users = {result4.data[0]['count']}")
        
        # Demonstrate batch execution
        print("\n⚡ Executing batch queries...")
        batch_queries = [
            "SELECT COUNT(*) FROM users",
            "SELECT COUNT(*) FROM departments",
            "SELECT COUNT(*) FROM orders"
        ]
        batch_results = await adapter.execute_batch(batch_queries)
        print(f"✅ Batch execution: {len(batch_results)} queries completed")
        
        # Demonstrate table information
        print("\n📋 Getting detailed table information...")
        users_table = await adapter.get_table_info("users")
        print(f"✅ Users table: {len(users_table.columns)} columns")
        print(f"   📝 Schema: {users_table.schema}")
        print(f"   🏷️ Business domain: {users_table.business_domain}")
        print(f"   📊 Row count: {users_table.row_count}")
        print(f"   💾 Size: {users_table.size_bytes} bytes")
        
        for column in users_table.columns:
            pk_marker = " 🔑" if column.is_primary_key else ""
            fk_marker = " 🔗" if column.is_foreign_key else ""
            unique_marker = " ⭐" if column.is_unique else ""
            print(f"   📝 {column.name} ({column.data_type}){pk_marker}{fk_marker}{unique_marker}")
        
        # Demonstrate foreign key relationships
        print("\n🔗 Foreign key relationships:")
        for fk in users_table.foreign_keys:
            print(f"   {users_table.schema}.{users_table.name}.{fk.column_name} → {fk.referenced_table}.{fk.referenced_column}")
        
        # Demonstrate indexes
        print("\n📊 Indexes:")
        for index in users_table.indexes:
            clustered_marker = " (Clustered)" if index.is_clustered else ""
            unique_marker = " (Unique)" if index.is_unique else ""
            print(f"   📈 {index.name}: {', '.join(index.columns)}{clustered_marker}{unique_marker}")
        
        # Demonstrate query validation
        print("\n✅ Validating SQL queries...")
        valid_queries = [
            "SELECT * FROM users",
            "INSERT INTO users (name, email) VALUES ('Test', 'test@example.com')",
            "UPDATE users SET age = 26 WHERE id = 1",
            "DELETE FROM users WHERE id = 1",
            "CREATE TABLE test_table (id int PRIMARY KEY)",
            "ALTER TABLE users ADD COLUMN phone varchar(20)",
            "DROP TABLE test_table"
        ]
        
        for query in valid_queries:
            is_valid = await adapter.validate_query(query)
            print(f"   {'✅' if is_valid else '❌'} {query[:40]}...")
        
        # Demonstrate query planning
        print("\n📈 Getting query execution plan...")
        plan = await adapter.get_query_plan("SELECT * FROM users WHERE age > 25")
        print(f"✅ Plan type: {plan.plan_type}")
        print(f"✅ Estimated cost: {plan.cost}")
        print(f"✅ Estimated rows: {plan.rows_estimated}")
        print(f"✅ Execution time: {plan.execution_time}s")
        
        # Demonstrate utility methods
        print("\n🛠️ Using utility methods...")
        table_names = await adapter.get_table_names()
        print(f"✅ Table names: {', '.join(table_names)}")
        
        user_columns = await adapter.get_column_names("users")
        print(f"✅ User columns: {', '.join(user_columns)}")
        
        user_count = await adapter.get_table_row_count("users")
        print(f"✅ User count: {user_count}")
        
        user_size = await adapter.get_table_size("users")
        print(f"✅ User table size: {user_size} bytes")
        
        # Demonstrate context manager
        print("\n🔄 Testing context manager...")
        async with MockSQLServerAdapter(config) as ctx_adapter:
            result = await ctx_adapter.execute_query("SELECT COUNT(*) FROM users")
            print(f"✅ Context manager: {result.data[0]['count']} users found")
        
        print("\n🎉 SQL Server adapter demonstration completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Disconnect
        if adapter.is_connected:
            await adapter.disconnect()
            print("\n🔌 Disconnected from SQL Server")


async def demonstrate_sqlserver_features():
    """Demonstrate SQL Server specific features."""
    
    print("\n🔧 SQL Server Specific Features")
    print("=" * 40)
    
    config = ConnectionConfig(
        host="sqlserver.example.com",
        port=1433,
        database="puma_procurement",
        username="puma_user",
        password="puma_password",
        driver="ODBC Driver 17 for SQL Server",
        ssl_mode="require"
    )
    
    adapter = MockSQLServerAdapter(config)
    
    try:
        await adapter.connect()
        
        # Demonstrate SQL Server specific data types
        print("\n📊 SQL Server Data Types:")
        print("   • int, bigint, smallint, tinyint")
        print("   • decimal, numeric, money, smallmoney")
        print("   • varchar, nvarchar, char, nchar")
        print("   • datetime, datetime2, date, time")
        print("   • bit, binary, varbinary")
        print("   • uniqueidentifier, xml, json")
        
        # Demonstrate SQL Server specific features
        print("\n🚀 SQL Server Features:")
        print("   • Stored procedures and functions")
        print("   • Triggers and constraints")
        print("   • Indexes (clustered, non-clustered)")
        print("   • Views and materialized views")
        print("   • Full-text search")
        print("   • XML and JSON support")
        print("   • Temporal tables")
        print("   • Columnstore indexes")
        
        # Demonstrate connection string options
        print("\n🔗 Connection String Options:")
        print("   • Windows Authentication (Trusted_Connection=yes)")
        print("   • SQL Server Authentication (UID/PWD)")
        print("   • SSL/TLS encryption (Encrypt=yes)")
        print("   • Connection pooling")
        print("   • Timeout settings")
        print("   • Multiple driver support")
        
        # Demonstrate business domain detection
        print("\n🏢 Business Domain Detection:")
        domains = ["finance", "crm", "ecommerce", "procurement", "hr", "healthcare", "manufacturing"]
        for domain in domains:
            print(f"   • {domain.title()}: Detected from table/column names")
        
        await adapter.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def demonstrate_puma_integration():
    """Demonstrate Puma procurement integration example."""
    
    print("\n🛒 Puma Procurement Integration Example")
    print("=" * 45)
    
    # Puma-specific configuration
    config = ConnectionConfig(
        host="puma-sqlserver.company.com",
        port=1433,
        database="PumaProcurementDB",
        username="puma_rag_user",
        password="secure_password_123",
        driver="ODBC Driver 17 for SQL Server",
        ssl_mode="require",
        connection_timeout=30,
        pool_size=15,
        max_overflow=25
    )
    
    adapter = MockSQLServerAdapter(config)
    
    try:
        await adapter.connect()
        
        print(f"✅ Connected to Puma SQL Server: {config.host}")
        print(f"✅ Database: {config.database}")
        print(f"✅ User: {config.username}")
        
        # Simulate Puma procurement queries
        print("\n📋 Puma Procurement Queries:")
        
        # Query 1: Vendor performance
        print("   🔍 Query: 'Show me vendor performance metrics'")
        print("   📊 SQL: SELECT v.vendor_name, COUNT(po.po_id) as order_count, AVG(po.total_amount) as avg_amount")
        print("          FROM vendors v JOIN purchase_orders po ON v.vendor_id = po.vendor_id")
        print("          GROUP BY v.vendor_name ORDER BY order_count DESC")
        
        # Query 2: Purchase order trends
        print("\n   🔍 Query: 'What are the purchase order trends for Q4?'")
        print("   📊 SQL: SELECT MONTH(order_date) as month, COUNT(*) as po_count, SUM(total_amount) as total_value")
        print("          FROM purchase_orders WHERE YEAR(order_date) = 2024 AND MONTH(order_date) >= 10")
        print("          GROUP BY MONTH(order_date) ORDER BY month")
        
        # Query 3: Cost analysis
        print("\n   🔍 Query: 'Analyze costs by department and category'")
        print("   📊 SQL: SELECT d.dept_name, c.category_name, SUM(po.total_amount) as total_cost")
        print("          FROM purchase_orders po")
        print("          JOIN departments d ON po.dept_id = d.dept_id")
        print("          JOIN categories c ON po.category_id = c.category_id")
        print("          GROUP BY d.dept_name, c.category_name ORDER BY total_cost DESC")
        
        # Demonstrate visualization potential
        print("\n📈 Visualization Opportunities:")
        print("   • Vendor performance bar charts")
        print("   • Purchase order trend line graphs")
        print("   • Cost analysis pie charts")
        print("   • Department spending heatmaps")
        print("   • Monthly procurement dashboards")
        
        await adapter.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Run the demonstrations
    asyncio.run(demonstrate_sqlserver_adapter())
    asyncio.run(demonstrate_sqlserver_features())
    asyncio.run(demonstrate_puma_integration())
