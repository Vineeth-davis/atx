#!/usr/bin/env python3
"""
Script to clear the vector store for rebuilding.
"""

import sys
import os
sys.path.append('.')

def clear_vector_store():
    try:
        from rag.vector_store import VectorStore
        
        # Clear the puma_sqlserver namespace
        vs = VectorStore(namespace='puma_sqlserver')
        vs.clear_index()
        
        print("✅ Cleared vector store for puma_sqlserver namespace")
        
        # Check if it's cleared
        stats = vs.get_stats()
        print(f"Vector store stats: {stats}")
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    clear_vector_store()
