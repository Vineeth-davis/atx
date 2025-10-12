#!/usr/bin/env python3
"""
Test script for NL→SQL functionality with Puma SQL Server database.
This script tests the complete flow: connection → RAG initialization → NL→SQL generation.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from adapters.sqlserver_adapter import SQLServerAdapter
from adapters.database_adapter import ConnectionConfig
from rag.nl2sql import NL2SQLGenerator
from core.schema_introspector import SchemaIntrospector

async def test_puma_nl2sql():
    """Test NL→SQL functionality with Puma database"""
    print("🚀 Testing NL→SQL with Puma SQL Server Database")
    print("=" * 60)
    
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
    
    print(f"📊 Connecting to Puma database: {config.host}:{config.port}/{config.database}")
    
    # Step 1: Connect to database
    adapter = SQLServerAdapter(config)
    try:
        await adapter.connect()
        print("✅ Database connection successful")
        
        # Test connection
        is_connected = await adapter.test_connection()
        if is_connected:
            print("✅ Connection test passed")
        else:
            print("❌ Connection test failed")
            return
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Step 2: Initialize RAG system
    print("\n🔄 Initializing RAG system...")
    namespace = "puma_sqlserver"
    dialect = "sqlserver"
    
    try:
        # Create NL2SQL generator
        nl2sql_gen = NL2SQLGenerator(namespace=namespace, dialect=dialect)
        
        # Build schema documents from adapter
        print("📚 Building schema documents from Puma database...")
        await nl2sql_gen.schema_retriever.build_schema_documents(adapter)
        
        print("✅ RAG system initialized successfully")
        
    except Exception as e:
        print(f"❌ RAG initialization failed: {e}")
        return
    
    # Step 3: Test NL→SQL queries
    print("\n🤖 Testing NL→SQL queries...")
    
    test_questions = [
        "Show me all vendors and their contact information",
        "What is the total value of purchase orders by vendor?",
        "Which departments have the most purchase orders?",
        "Show me vendors with the highest order values",
        "What are the most recent purchase orders?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Test Query {i}: {question}")
        print("-" * 50)
        
        try:
            # Get schema context
            context = await nl2sql_gen.schema_retriever.retrieve_schema_context(question)
            print(f"📋 Retrieved {len(context)} schema context items")
            
            # Generate SQL
            result = await nl2sql_gen.generate_sql(question, context)
            
            if result.get('sql'):
                print(f"✅ SQL Generated:")
                print(f"SQL: {result['sql']}")
                print(f"Explanation: {result.get('explanation', 'No explanation')}")
                print(f"Confidence: {result.get('confidence', 0.0):.2f}")
                
                # Try to execute the query
                try:
                    query_result = await adapter.execute_query(result['sql'])
                    print(f"📊 Query executed successfully: {query_result.row_count} rows returned")
                    
                    if query_result.data and len(query_result.data) > 0:
                        print("📋 Sample data:")
                        for j, row in enumerate(query_result.data[:3]):  # Show first 3 rows
                            print(f"  Row {j+1}: {row}")
                        if len(query_result.data) > 3:
                            print(f"  ... and {len(query_result.data) - 3} more rows")
                    
                except Exception as e:
                    print(f"⚠️ Query execution failed: {e}")
                    
            else:
                print("❌ Failed to generate SQL")
                
        except Exception as e:
            print(f"❌ Error processing question: {e}")
    
    # Step 4: Test advanced queries
    print("\n🚀 Testing Advanced SQL queries...")
    
    advanced_questions = [
        "Rank vendors by total order value and show their percentile rankings",
        "Show me the running total of procurement spend over time",
        "Calculate the standard deviation of order values by department"
    ]
    
    for i, question in enumerate(advanced_questions, 1):
        print(f"\n📝 Advanced Query {i}: {question}")
        print("-" * 50)
        
        try:
            # Get schema context
            context = await nl2sql_gen.schema_retriever.retrieve_schema_context(question)
            
            # Generate SQL
            result = await nl2sql_gen.generate_sql(question, context)
            
            if result.get('sql'):
                print(f"✅ Advanced SQL Generated:")
                print(f"SQL: {result['sql']}")
                print(f"Explanation: {result.get('explanation', 'No explanation')}")
                print(f"Confidence: {result.get('confidence', 0.0):.2f}")
                
                # Try to execute the query
                try:
                    query_result = await adapter.execute_query(result['sql'])
                    print(f"📊 Query executed successfully: {query_result.row_count} rows returned")
                    
                except Exception as e:
                    print(f"⚠️ Advanced query execution failed: {e}")
                    
            else:
                print("❌ Failed to generate advanced SQL")
                
        except Exception as e:
            print(f"❌ Error processing advanced question: {e}")
    
    # Cleanup
    try:
        await adapter.disconnect()
        print("\n✅ Database connection closed")
    except Exception as e:
        print(f"⚠️ Error closing connection: {e}")
    
    print("\n🎉 NL→SQL testing completed!")

if __name__ == "__main__":
    asyncio.run(test_puma_nl2sql())
