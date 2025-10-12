"""
Database Adapter Framework - Usage Example

This example demonstrates how to use the database adapter framework
for universal database connectivity.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from adapters.database_adapter import (
    DatabaseAdapter,
    DatabaseType,
    ConnectionConfig,
    QueryResult,
    ColumnInfo,
    TableInfo,
    DatabaseSchema,
    QueryPlan,
    ForeignKeyInfo,
    SchemaError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExampleDatabaseAdapter(DatabaseAdapter):
    """
    Example implementation of DatabaseAdapter for demonstration purposes.
    This shows how to implement the abstract interface.
    """
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self._mock_data = {
            "users": [
                {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25},
                {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "age": 35}
            ],
            "orders": [
                {"id": 1, "user_id": 1, "product": "Laptop", "amount": 999.99, "date": "2024-01-15"},
                {"id": 2, "user_id": 2, "product": "Mouse", "amount": 29.99, "date": "2024-01-16"},
                {"id": 3, "user_id": 1, "product": "Keyboard", "amount": 79.99, "date": "2024-01-17"}
            ]
        }
    
    @property
    def database_type(self) -> DatabaseType:
        return DatabaseType.POSTGRESQL
    
    async def connect(self) -> bool:
        """Simulate database connection."""
        logger.info(f"Connecting to {self.database_type.value} database: {self.config.database}")
        self.is_connected = True
        return True
    
    async def disconnect(self) -> bool:
        """Simulate database disconnection."""
        logger.info("Disconnecting from database")
        self.is_connected = False
        return True
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> QueryResult:
        """Simulate query execution with mock data."""
        if not self.is_connected:
            raise ConnectionError("Not connected to database")
        
        logger.info(f"Executing query: {query}")
        
        # Simple query parsing for demonstration
        query_lower = query.lower().strip()
        
        if "select * from users" in query_lower:
            data = self._mock_data["users"]
            columns = ["id", "name", "email", "age"]
        elif "select * from orders" in query_lower:
            data = self._mock_data["orders"]
            columns = ["id", "user_id", "product", "amount", "date"]
        elif "select count(*) from users" in query_lower:
            data = [{"count": len(self._mock_data["users"])}]
            columns = ["count"]
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
            metadata={"database": "example", "query_type": "select"}
        )
    
    async def execute_batch(self, queries: List[str]) -> List[QueryResult]:
        """Execute multiple queries in batch."""
        results = []
        for query in queries:
            result = await self.execute_query(query)
            results.append(result)
        return results
    
    async def get_schema(self, force_refresh: bool = False) -> DatabaseSchema:
        """Get mock database schema."""
        tables = [
            TableInfo(
                name="users",
                schema="public",
                columns=[
                    ColumnInfo(name="id", data_type="integer", is_nullable=False, is_primary_key=True),
                    ColumnInfo(name="name", data_type="varchar", is_nullable=False),
                    ColumnInfo(name="email", data_type="varchar", is_nullable=False, is_unique=True),
                    ColumnInfo(name="age", data_type="integer", is_nullable=True)
                ],
                primary_keys=["id"],
                foreign_keys=[],
                indexes=[],
                row_count=len(self._mock_data["users"]),
                size_bytes=1024,
                description="User information table",
                business_domain="crm"
            ),
            TableInfo(
                name="orders",
                schema="public",
                columns=[
                    ColumnInfo(name="id", data_type="integer", is_nullable=False, is_primary_key=True),
                    ColumnInfo(name="user_id", data_type="integer", is_nullable=False, is_foreign_key=True),
                    ColumnInfo(name="product", data_type="varchar", is_nullable=False),
                    ColumnInfo(name="amount", data_type="decimal", is_nullable=False),
                    ColumnInfo(name="date", data_type="date", is_nullable=False)
                ],
                primary_keys=["id"],
                foreign_keys=[
                    ForeignKeyInfo(
                        column_name="user_id",
                        referenced_table="users",
                        referenced_column="id",
                        constraint_name="fk_orders_user_id"
                    )
                ],
                indexes=[],
                row_count=len(self._mock_data["orders"]),
                size_bytes=2048,
                description="Order information table",
                business_domain="ecommerce"
            )
        ]
        
        return DatabaseSchema(
            database_name=self.config.database,
            tables=tables,
            views=[],
            functions=[],
            procedures=[],
            total_size_bytes=3072,
            version="Example DB 1.0.0",
            description="Example database for demonstration"
        )
    
    async def get_table_info(self, table_name: str, schema: Optional[str] = None) -> TableInfo:
        """Get information about a specific table."""
        schema_info = await self.get_schema()
        for table in schema_info.tables:
            if table.name == table_name:
                return table
        raise SchemaError(f"Table {table_name} not found")
    
    async def get_table_data(self, table_name: str, limit: int = 100, offset: int = 0, 
                           schema: Optional[str] = None) -> QueryResult:
        """Get sample data from a table."""
        return await self.execute_query(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}")
    
    async def validate_query(self, query: str) -> bool:
        """Validate query syntax."""
        query_lower = query.lower().strip()
        return query_lower.startswith(('select', 'insert', 'update', 'delete'))
    
    async def get_query_plan(self, query: str) -> QueryPlan:
        """Get mock query execution plan."""
        return QueryPlan(
            plan_type="Mock Plan",
            cost=1.0,
            rows_estimated=100,
            execution_time=0.001,
            details={"type": "mock", "table": "users"}
        )
    
    async def test_connection(self) -> bool:
        """Test database connectivity."""
        return self.is_connected
    
    async def _get_version(self) -> str:
        """Get database version."""
        return "Example DB 1.0.0"


async def demonstrate_database_adapter():
    """Demonstrate the database adapter framework."""
    
    print("🚀 Database Adapter Framework Demonstration")
    print("=" * 50)
    
    # Create connection configuration
    config = ConnectionConfig(
        host="localhost",
        port=5432,
        database="example_db",
        username="demo_user",
        password="demo_password"
    )
    
    # Create adapter instance
    adapter = ExampleDatabaseAdapter(config)
    
    try:
        # Demonstrate connection
        print("\n📡 Connecting to database...")
        await adapter.connect()
        print(f"✅ Connected to {adapter.database_type.value} database")
        
        # Demonstrate schema retrieval
        print("\n📊 Retrieving database schema...")
        schema = await adapter.get_schema()
        print(f"✅ Database: {schema.database_name}")
        print(f"✅ Version: {schema.version}")
        print(f"✅ Tables: {len(schema.tables)}")
        
        for table in schema.tables:
            print(f"   📋 {table.name} ({table.business_domain}) - {table.row_count} rows")
        
        # Demonstrate query execution
        print("\n🔍 Executing sample queries...")
        
        # Query 1: Get all users
        result1 = await adapter.execute_query("SELECT * FROM users")
        print(f"✅ Query 1: Found {result1.row_count} users")
        for row in result1.data[:2]:  # Show first 2 rows
            print(f"   👤 {row['name']} ({row['email']})")
        
        # Query 2: Get all orders
        result2 = await adapter.execute_query("SELECT * FROM orders")
        print(f"✅ Query 2: Found {result2.row_count} orders")
        for row in result2.data[:2]:  # Show first 2 rows
            print(f"   🛒 Order {row['id']}: {row['product']} - ${row['amount']}")
        
        # Query 3: Count users
        result3 = await adapter.execute_query("SELECT COUNT(*) FROM users")
        print(f"✅ Query 3: Total users = {result3.data[0]['count']}")
        
        # Demonstrate batch execution
        print("\n⚡ Executing batch queries...")
        batch_queries = [
            "SELECT COUNT(*) FROM users",
            "SELECT COUNT(*) FROM orders"
        ]
        batch_results = await adapter.execute_batch(batch_queries)
        print(f"✅ Batch execution: {len(batch_results)} queries completed")
        
        # Demonstrate table information
        print("\n📋 Getting table information...")
        users_table = await adapter.get_table_info("users")
        print(f"✅ Users table: {len(users_table.columns)} columns")
        for column in users_table.columns:
            pk_marker = " 🔑" if column.is_primary_key else ""
            print(f"   📝 {column.name} ({column.data_type}){pk_marker}")
        
        # Demonstrate query validation
        print("\n✅ Validating queries...")
        valid_queries = [
            "SELECT * FROM users",
            "INSERT INTO users VALUES (1, 'Test', 'test@example.com', 25)",
            "UPDATE users SET age = 26 WHERE id = 1"
        ]
        
        for query in valid_queries:
            is_valid = await adapter.validate_query(query)
            print(f"   {'✅' if is_valid else '❌'} {query[:30]}...")
        
        # Demonstrate query planning
        print("\n📈 Getting query execution plan...")
        plan = await adapter.get_query_plan("SELECT * FROM users WHERE age > 25")
        print(f"✅ Plan type: {plan.plan_type}")
        print(f"✅ Estimated cost: {plan.cost}")
        print(f"✅ Estimated rows: {plan.rows_estimated}")
        
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
        async with ExampleDatabaseAdapter(config) as ctx_adapter:
            result = await ctx_adapter.execute_query("SELECT COUNT(*) FROM users")
            print(f"✅ Context manager: {result.data[0]['count']} users found")
        
        print("\n🎉 Database adapter framework demonstration completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Disconnect
        if adapter.is_connected:
            await adapter.disconnect()
            print("\n🔌 Disconnected from database")


async def demonstrate_error_handling():
    """Demonstrate error handling capabilities."""
    
    print("\n🛡️ Error Handling Demonstration")
    print("=" * 40)
    
    config = ConnectionConfig(
        host="localhost",
        port=5432,
        database="test_db",
        username="test_user",
        password="test_password"
    )
    
    adapter = ExampleDatabaseAdapter(config)
    
    try:
        # Try to execute query without connection
        print("🔍 Testing query without connection...")
        await adapter.execute_query("SELECT * FROM users")
    except ConnectionError as e:
        print(f"✅ Caught expected ConnectionError: {e}")
    
    try:
        # Try to get non-existent table
        await adapter.connect()
        print("\n🔍 Testing non-existent table...")
        await adapter.get_table_info("non_existent_table")
    except SchemaError as e:
        print(f"✅ Caught expected SchemaError: {e}")
    
    # Test invalid query validation
    print("\n🔍 Testing invalid query validation...")
    is_valid = await adapter.validate_query("INVALID SQL STATEMENT")
    print(f"✅ Invalid query correctly identified: {not is_valid}")
    
    await adapter.disconnect()


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(demonstrate_database_adapter())
    asyncio.run(demonstrate_error_handling())
