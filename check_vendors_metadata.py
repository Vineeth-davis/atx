#!/usr/bin/env python3
"""
Script to check Vendors table metadata specifically.
"""

import sys
import os
sys.path.append('.')

def check_vendors_metadata():
    try:
        from rag.vector_store import VectorStore
        
        # Load the vector store
        vs = VectorStore(namespace='puma_sqlserver')
        
        # Look for Vendors table specifically
        vendors_items = [item for item in vs.metadata if 'Vendors' in item.get('table', '')]
        print(f'Vendors-related items: {len(vendors_items)}')
        
        # Show all Vendors-related items
        for i, item in enumerate(vendors_items):
            print(f'{i+1}. Type: {item.get("type")}, Table: {item.get("table")}, Column: {item.get("column")}')
        
        # Look for exact match
        exact_vendors = [item for item in vs.metadata if item.get('table') == 'dbo.Vendors']
        print(f'\nExact dbo.Vendors items: {len(exact_vendors)}')
        for item in exact_vendors[:5]:
            print(f'Type: {item.get("type")}, Table: {item.get("table")}, Column: {item.get("column")}')
            
        # Look for columns in Vendors table
        vendors_columns = [item for item in vs.metadata if item.get('table') == 'dbo.Vendors' and item.get('type') == 'column']
        print(f'\nVendors columns: {len(vendors_columns)}')
        for item in vendors_columns[:10]:
            print(f'Column: {item.get("column")}, Type: {item.get("data_type")}')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_vendors_metadata()
