#!/usr/bin/env python3
"""
Script to debug connection issues.
"""

import sys
import os
sys.path.append('.')

async def test_connection_debug():
    try:
        from adapters.sqlserver_adapter import SQLServerAdapter, ConnectionConfig
        
        config = ConnectionConfig(
            host='98.70.24.81',
            port=1433,
            database='puma_test',
            username='vineeth',
            password='Fish4Lake$9',
            driver='ODBC Driver 18 for SQL Server',
            ssl_mode=None
        )
        
        print("Creating adapter...")
        adapter = SQLServerAdapter(config)
        
        print("Building connection string...")
        conn_str = adapter._build_connection_string()
        print(f"Connection string: {conn_str}")
        
        print("Connecting...")
        connected = await adapter.connect()
        print(f"Connected: {connected}")
        print(f"Is connected: {adapter.is_connected}")
        
        if connected:
            print("Getting schema...")
            schema = await adapter.get_schema()
            print(f"Schema has {len(schema.tables)} tables")
            
            # Test a simple query
            print("Testing simple query...")
            result = await adapter.execute_query("SELECT TOP 1 * FROM [dbo].[Vendors]")
            print(f"Query result: {result.row_count} rows")
            
            # Disconnect
            print("Disconnecting...")
            await adapter.disconnect()
            print(f"Is connected after disconnect: {adapter.is_connected}")
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_connection_debug())
