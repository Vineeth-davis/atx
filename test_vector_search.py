#!/usr/bin/env python3
"""
Script to test vector store search for Vendors columns.
"""

import sys
import os
sys.path.append('.')

async def test_vector_search():
    try:
        from rag.vector_store import VectorStore
        from rag.embeddings import embedding_service
        
        # Load the vector store
        vs = VectorStore(namespace='puma_sqlserver')
        
        # Get Vendors column documents
        vendors_columns = [item for item in vs.metadata if item.get('table') == 'dbo.Vendors' and item.get('type') == 'column']
        print(f'Vendors columns in vector store: {len(vendors_columns)}')
        
        # Show first few column documents
        for i, item in enumerate(vendors_columns[:5]):
            print(f'{i+1}. Column: {item.get("column")}, Type: {item.get("data_type")}, Description: {item.get("description")}')
        
        # Test search for 'vendors' query
        print(f'\n=== Testing search for "vendors" ===')
        query_embedding = await embedding_service.generate_single_embedding('vendors')
        results = vs.search(query_embedding, k=10)
        
        print(f'Search results: {len(results)}')
        for i, result in enumerate(results[:5]):
            metadata = result['metadata']
            print(f'{i+1}. Type: {metadata.get("type")}, Table: {metadata.get("table")}, Column: {metadata.get("column")}, Score: {result["score"]:.3f}')
            
        # Test search for 'vendor names' query
        print(f'\n=== Testing search for "vendor names" ===')
        query_embedding2 = await embedding_service.generate_single_embedding('vendor names')
        results2 = vs.search(query_embedding2, k=10)
        
        print(f'Search results: {len(results2)}')
        for i, result in enumerate(results2[:5]):
            metadata = result['metadata']
            print(f'{i+1}. Type: {metadata.get("type")}, Table: {metadata.get("table")}, Column: {metadata.get("column")}, Score: {result["score"]:.3f}')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_vector_search())
