#!/usr/bin/env python3
"""
Script to manually rebuild the RAG system with improved column documents.
"""

import sys
import os
sys.path.append('.')

async def rebuild_rag_manual():
    try:
        from adapters.sqlserver_adapter import SQLServerAdapter, ConnectionConfig
        from rag.nl2sql import NL2SQLGenerator
        
        print("=== Manually Rebuilding RAG System ===")
        
        # Create connection config
        config = ConnectionConfig(
            host='98.70.24.81',
            port=1433,
            database='puma_test',
            username='vineeth',
            password='Fish4Lake$9',
            driver='ODBC Driver 18 for SQL Server',
            ssl_mode=None
        )
        
        # Create adapter
        print("Creating SQL Server adapter...")
        adapter = SQLServerAdapter(config)
        
        # Connect
        print("Connecting to database...")
        connected = await adapter.connect()
        if not connected:
            print("❌ Failed to connect to database")
            return
        
        print("✅ Connected to database")
        
        # Create NL2SQL generator
        print("Creating NL2SQL generator...")
        nl2sql_gen = NL2SQLGenerator(namespace='puma_sqlserver', dialect='sqlserver')
        
        # Build schema documents
        print("Building schema documents...")
        await nl2sql_gen.schema_retriever.build_schema_documents(adapter)
        
        print("✅ RAG system rebuilt successfully!")
        
        # Verify the rebuild
        print("\n=== Verifying Rebuild ===")
        context = await nl2sql_gen.schema_retriever.retrieve_schema_context('show me all vendors', k=10)
        
        table_items = [item for item in context if item.get('type') == 'table']
        column_items = [item for item in context if item.get('type') == 'column']
        
        print(f"Retrieved {len(context)} context items")
        print(f"Table items: {len(table_items)}, Column items: {len(column_items)}")
        
        if column_items:
            print("✅ SUCCESS: Column information is being retrieved!")
        else:
            print("❌ ISSUE: No column information retrieved")
        
        # Disconnect
        await adapter.disconnect()
        print("✅ Disconnected from database")
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(rebuild_rag_manual())
