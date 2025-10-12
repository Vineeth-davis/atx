#!/usr/bin/env python3
"""
Script to debug schema context retrieval.
"""

import sys
import os
sys.path.append('.')

async def debug_retrieval():
    try:
        from rag.retriever import SchemaRetriever
        
        retriever = SchemaRetriever(namespace='puma_sqlserver')
        
        # Test with different queries
        queries = ['show me all vendors', 'vendors', 'vendor names', 'dbo.Vendors']
        
        for query in queries:
            print(f'\n=== Query: {query} ===')
            context = await retriever.retrieve_schema_context(query, k=20)
            print(f'Retrieved {len(context)} items')
            
            # Count by type
            table_items = [item for item in context if item.get('type') == 'table']
            column_items = [item for item in context if item.get('type') == 'column']
            print(f'Table items: {len(table_items)}, Column items: {len(column_items)}')
            
            # Show first few items
            for i, item in enumerate(context[:5]):
                print(f'{i+1}. Type: {item.get("type")}, Table: {item.get("table")}, Column: {item.get("column")}')
                
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_retrieval())
