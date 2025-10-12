#!/usr/bin/env python3
"""
Script to verify that the RAG system has been rebuilt with proper column documents.
"""

import sys
import os
sys.path.append('.')

async def verify_rag_rebuild():
    try:
        from rag.vector_store import VectorStore
        from rag.retriever import SchemaRetriever
        
        print("=== Verifying RAG System Rebuild ===")
        
        # Check vector store stats
        vs = VectorStore(namespace='puma_sqlserver')
        stats = vs.get_stats()
        print(f"Vector store stats: {stats}")
        
        if stats['total_vectors'] == 0:
            print("❌ Vector store is empty - RAG system not rebuilt yet")
            print("Please go to Streamlit UI and click '3️⃣ Initialize RAG'")
            return
        
        # Check Vendors table information
        vendors_items = [item for item in vs.metadata if item.get('table') == 'dbo.Vendors']
        print(f"\nVendors table items: {len(vendors_items)}")
        
        # Check column information
        vendors_columns = [item for item in vs.metadata if item.get('table') == 'dbo.Vendors' and item.get('type') == 'column']
        print(f"Vendors column items: {len(vendors_columns)}")
        
        # Show sample column information
        if vendors_columns:
            print("\nSample Vendors columns:")
            for i, item in enumerate(vendors_columns[:5]):
                print(f"{i+1}. Column: {item.get('column')}, Type: {item.get('data_type')}")
        
        # Test schema retrieval
        print("\n=== Testing Schema Retrieval ===")
        retriever = SchemaRetriever(namespace='puma_sqlserver')
        context = await retriever.retrieve_schema_context('show me all vendors', k=10)
        
        print(f"Retrieved {len(context)} context items")
        
        # Count by type
        table_items = [item for item in context if item.get('type') == 'table']
        column_items = [item for item in context if item.get('type') == 'column']
        print(f"Table items: {len(table_items)}, Column items: {len(column_items)}")
        
        # Show sample context
        print("\nSample context items:")
        for i, item in enumerate(context[:5]):
            print(f"{i+1}. Type: {item.get('type')}, Table: {item.get('table')}, Column: {item.get('column')}")
        
        if column_items:
            print("\n✅ SUCCESS: Column information is being retrieved!")
            print("The RAG system has been rebuilt with proper column documents.")
        else:
            print("\n❌ ISSUE: No column information retrieved")
            print("The column documents may not be searchable enough.")
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(verify_rag_rebuild())
