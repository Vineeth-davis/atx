#!/usr/bin/env python3
"""
Script to check what's in the vector store for debugging.
"""

import sys
import os
sys.path.append('.')

def check_vector_store():
    try:
        from rag.vector_store import VectorStore
        from rag.embeddings import embedding_service
        
        # Load the vector store
        vs = VectorStore()
        
        # Check what's in the puma namespace
        print('=== PUMA NAMESPACE CONTENT ===')
        
        # Get some sample vectors to see what's stored
        index = vs._indexes.get('puma_sqlserver')
        if index:
            print(f'Index size: {index.ntotal}')
            # Get a few vectors to see metadata
            if index.ntotal > 0:
                vectors, indices = index.search(embedding_service.generate_single_embedding('vendor'), 5)
                for i, idx in enumerate(indices[0]):
                    if idx < len(vs._metadata.get('puma_sqlserver', [])):
                        metadata = vs._metadata['puma_sqlserver'][idx]
                        print(f'{i+1}. Type: {metadata.get("type", "unknown")}, Table: {metadata.get("table", "unknown")}, Column: {metadata.get("column", "unknown")}')
        else:
            print('No puma_sqlserver index found')
            
        print('\n=== AVAILABLE NAMESPACES ===')
        for namespace in vs._indexes.keys():
            print(f'- {namespace}')
            
        # Check metadata for puma namespace
        if 'puma_sqlserver' in vs._metadata:
            print(f'\n=== PUMA METADATA SAMPLE ===')
            metadata_list = vs._metadata['puma_sqlserver']
            for i, metadata in enumerate(metadata_list[:10]):  # Show first 10
                print(f'{i+1}. {metadata}')
                
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_vector_store()
