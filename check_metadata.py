#!/usr/bin/env python3
"""
Script to check what metadata is stored in the vector store.
"""

import sys
import os
sys.path.append('.')

def check_metadata():
    try:
        from rag.vector_store import VectorStore
        
        # Load the vector store
        vs = VectorStore(namespace='puma_sqlserver')
        
        # Check what's in the metadata
        if vs.metadata:
            print(f'Total metadata items: {len(vs.metadata)}')
            
            # Look for column information
            column_items = [item for item in vs.metadata if item.get('type') == 'column']
            print(f'Column items: {len(column_items)}')
            
            # Show first few column items
            for i, item in enumerate(column_items[:5]):
                print(f'{i+1}. Table: {item.get("table")}, Column: {item.get("column")}, Type: {item.get("data_type")}')
                
            # Look for Vendors table specifically
            vendors_items = [item for item in vs.metadata if 'Vendors' in item.get('table', '')]
            print(f'\nVendors-related items: {len(vendors_items)}')
            for item in vendors_items[:3]:
                print(f'Type: {item.get("type")}, Table: {item.get("table")}, Column: {item.get("column")}')
        else:
            print('No metadata found')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_metadata()
