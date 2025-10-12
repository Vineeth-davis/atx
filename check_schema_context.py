#!/usr/bin/env python3
"""
Script to check what schema context is being retrieved for debugging.
"""

import sys
import os
sys.path.append('.')

async def check_schema_context():
    try:
        from rag.retriever import SchemaRetriever
        
        retriever = SchemaRetriever(namespace='puma_sqlserver')
        context = await retriever.retrieve_schema_context('show me all vendors')
        
        print(f'Retrieved {len(context)} context items:')
        for i, item in enumerate(context):
            print(f'{i+1}. Type: {item.get("type")}, Table: {item.get("table")}, Column: {item.get("column")}, Description: {item.get("description")}')
            
        # Also check what's in the vector store
        print(f'\nVector store stats: {retriever.vector_store.get_stats()}')
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_schema_context())
