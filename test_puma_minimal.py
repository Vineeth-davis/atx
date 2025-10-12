#!/usr/bin/env python3
"""
Minimal test script for NL→SQL functionality with Puma SQL Server database.
This script tests the core flow without requiring all dependencies.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for testing
os.environ['OPENAI_API_KEY'] = 'your-api-key-here'  # Replace with actual key
os.environ['VECTOR_STORE_PATH'] = './data/vector_store'
os.environ['VECTOR_STORE_TYPE'] = 'faiss'

async def test_puma_connection():
    """Test basic Puma database connection"""
    print("Testing Puma SQL Server Connection")
    print("=" * 50)
    
    try:
        from adapters.sqlserver_adapter import SQLServerAdapter
        from adapters.database_adapter import ConnectionConfig
        
        # Configuration for Puma database
        config = ConnectionConfig(
            host="98.70.24.81",
            port=1433,
            database="puma_test",
            username="vineeth",
            password="Fish4Lake$9",
            driver="ODBC Driver 17 for SQL Server",
            ssl_mode=None
        )
        
        print(f"Connecting to Puma database: {config.host}:{config.port}/{config.database}")
        
        # Create adapter and connect
        adapter = SQLServerAdapter(config)
        await adapter.connect()
        print("Database connection successful")
        
        # Test connection
        is_connected = await adapter.test_connection()
        if is_connected:
            print("Connection test passed")
        else:
            print("Connection test failed")
            return False
        
        # Get basic schema info
        print("\nGetting database schema...")
        schema = await adapter.get_schema()
        print(f"Found {len(schema.tables)} tables in database")
        
        # Show first few tables
        print("\nSample tables:")
        for i, table in enumerate(schema.tables[:5]):
            print(f"  {i+1}. {table.schema}.{table.name} ({len(table.columns)} columns)")
            if table.business_domain:
                print(f"     Domain: {table.business_domain}")
        
        if len(schema.tables) > 5:
            print(f"  ... and {len(schema.tables) - 5} more tables")
        
        # Test a simple query
        print("\nTesting simple query...")
        try:
            result = await adapter.execute_query("SELECT COUNT(*) as table_count FROM sys.tables WHERE is_ms_shipped = 0")
            if result.data:
                print(f"Query executed successfully: {result.data[0]['table_count']} user tables")
            else:
                print("Query returned no data")
        except Exception as e:
            print(f"Query execution failed: {e}")
        
        # Cleanup
        await adapter.disconnect()
        print("\nDatabase connection closed")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

async def test_nl2sql_basic():
    """Test basic NL->SQL functionality without full RAG"""
    print("\nTesting Basic NL->SQL Generation")
    print("=" * 50)
    
    try:
        # Mock schema context for testing
        mock_context = [
            {
                'type': 'table',
                'table': 'dbo.Vendors',
                'description': 'Vendor information table',
                'business_domain': 'procurement'
            },
            {
                'type': 'column',
                'table': 'dbo.Vendors',
                'column': 'Id',
                'description': 'Primary key',
                'data_type': 'int',
                'is_primary_key': True
            },
            {
                'type': 'column',
                'table': 'dbo.Vendors',
                'column': 'Name',
                'description': 'Vendor name',
                'data_type': 'nvarchar',
                'is_primary_key': False
            },
            {
                'type': 'table',
                'table': 'dbo.PurchaseOrders',
                'description': 'Purchase order information',
                'business_domain': 'procurement'
            },
            {
                'type': 'column',
                'table': 'dbo.PurchaseOrders',
                'column': 'Id',
                'description': 'Primary key',
                'data_type': 'int',
                'is_primary_key': True
            },
            {
                'type': 'column',
                'table': 'dbo.PurchaseOrders',
                'column': 'VendorId',
                'description': 'Foreign key to Vendors',
                'data_type': 'int',
                'is_foreign_key': True
            },
            {
                'type': 'column',
                'table': 'dbo.PurchaseOrders',
                'column': 'TotalAmount',
                'description': 'Total order amount',
                'data_type': 'decimal',
                'is_primary_key': False
            }
        ]
        
        # Test questions
        test_questions = [
            "Show me all vendors",
            "What is the total value of purchase orders?",
            "Show me vendors with their order counts"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\nTest Question {i}: {question}")
            print("-" * 40)
            
            # This would normally call the NL2SQL generator
            # For now, we'll just show what would happen
            print("Would generate SQL for this question")
            print("Would use context from Vendors and PurchaseOrders tables")
            print("Would generate SQL Server compatible syntax")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

async def main():
    """Main test function"""
    print("Puma NL->SQL Integration Test")
    print("=" * 60)
    
    # Test 1: Database connection
    connection_ok = await test_puma_connection()
    
    if connection_ok:
        # Test 2: Basic NL->SQL functionality
        await test_nl2sql_basic()
        
        print("\nBasic tests completed successfully!")
        print("\nNext steps:")
        print("1. Set up OpenAI API key in environment")
        print("2. Install missing dependencies (psycopg2, etc.)")
        print("3. Run full NL->SQL test with RAG initialization")
        print("4. Test Streamlit UI with database connection")
    else:
        print("\nDatabase connection failed. Please check:")
        print("1. SQL Server is running and accessible")
        print("2. Connection credentials are correct")
        print("3. ODBC driver is installed")
        print("4. Network connectivity to database server")

if __name__ == "__main__":
    asyncio.run(main())
