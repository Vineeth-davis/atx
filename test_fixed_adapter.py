"""
Test Fixed SQL Server Adapter

This script tests the fixed connection pool issue in the SQL Server adapter.
"""

import asyncio
import sys
from datetime import datetime

# Add current directory to Python path
sys.path.append('.')

from adapters.sqlserver_adapter import SQLServerAdapter
from adapters.database_adapter import ConnectionConfig
from core.schema_introspector import get_schema_introspector

async def test_fixed_adapter():
    """Test the fixed SQL Server adapter."""
    
    print("🔧 Testing Fixed SQL Server Adapter")
    print("=" * 50)
    
    # Configure connection
    config = ConnectionConfig(
        host="98.70.24.81",
        port=1433,
        database="puma_test",
        username="vineeth",
        password="Fish4Lake$9",
        driver="ODBC Driver 17 for SQL Server",
        connection_timeout=30,
        pool_size=5,
        max_overflow=10
    )
    
    adapter = SQLServerAdapter(config)
    
    try:
        print("🔌 Testing connection...")
        success = await adapter.connect()
        
        if not success:
            print("❌ Connection failed")
            return False
        
        print("✅ Connection successful!")
        
        # Test basic query
        print("\n🔍 Testing basic query...")
        result = await adapter.execute_query("SELECT DB_NAME() as database_name, @@VERSION as sql_version")
        
        print(f"✅ Query executed successfully!")
        print(f"   Rows: {result.row_count}")
        print(f"   Execution time: {result.execution_time:.3f}s")
        print(f"   Data: {result.data}")
        
        # Test table count query
        print("\n🔍 Testing table count query...")
        result = await adapter.execute_query("SELECT COUNT(*) as table_count FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        
        print(f"✅ Table count query executed!")
        print(f"   Rows: {result.row_count}")
        print(f"   Execution time: {result.execution_time:.3f}s")
        print(f"   Table count: {result.data[0]['table_count']}")
        
        # Test schema introspection
        print("\n🔍 Testing schema introspection...")
        introspector = get_schema_introspector()
        analysis = await introspector.analyze_schema(adapter)
        
        print(f"✅ Schema introspection completed!")
        print(f"   Database: {analysis.database_name}")
        print(f"   Tables: {analysis.total_tables}")
        print(f"   Columns: {analysis.total_columns}")
        print(f"   Relationships: {analysis.total_relationships}")
        print(f"   Data Quality: {analysis.data_quality_score:.2f}/1.0")
        print(f"   Complexity: {analysis.complexity_score:.2f}/1.0")
        
        # Show business domains
        if analysis.business_domains:
            print(f"\n🎯 Detected Business Domains:")
            for domain, tables in analysis.business_domains.items():
                print(f"   📊 {domain.value.upper()}: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")
        
        # Show key relationships
        if analysis.relationships:
            print(f"\n🔗 Key Relationships:")
            for i, rel in enumerate(analysis.relationships[:5], 1):
                print(f"   {i}. {rel.source_table} → {rel.target_table} ({rel.relationship_type.value})")
        
        await adapter.disconnect()
        print("\n✅ All tests completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_fixed_adapter())
