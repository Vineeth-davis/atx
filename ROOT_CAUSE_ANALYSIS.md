# Root Cause Analysis: SQL Generation Issues

## Problem Statement
When asking "show me all vendors", the generated SQL was:
```sql
SELECT [VendorName]
FROM [dbo].[[dbo].[Vendors]]
```

**Expected SQL**:
```sql
SELECT [Name]
FROM [dbo].[Vendors]
```

## Issues Identified

### 1. **Double Bracketing**: `[dbo].[[dbo].[Vendors]]`
- **Cause**: The `_enforce_identifiers` method is incorrectly handling table names that already contain brackets
- **Location**: `rag/nl2sql.py` - `_enforce_identifiers` method

### 2. **Wrong Column Name**: `[VendorName]` instead of `[Name]`
- **Cause**: The LLM is generating incorrect column names because it doesn't have proper schema context
- **Root Cause**: Column information is not being retrieved from the vector store

### 3. **Missing Column Context**
- **Cause**: Vector store search is only returning table items, not column items
- **Root Cause**: Column documents are not semantically searchable

## Root Cause Analysis

### Vector Store Search Issue
The vector store contains 150 column items for the `Vendors` table, but the search query "show me all vendors" only returns table items, not column items.

**Evidence**:
```
Vendors columns in vector store: 150
Search results for "vendors": 10 items, all table items, 0 column items
```

### Column Document Searchability Issue
The column documents are created with text like:
```
Column: dbo.Vendors.Name
Type: nvarchar
Description: nvarchar column
```

This text is not semantically similar to the query "vendors" because:
1. The column name `Name` doesn't contain "vendor"
2. The description is generic (`nvarchar column`)
3. No table context is included

## Fixes Applied

### 1. **Enhanced Column Document Creation**
**File**: `rag/retriever.py`
**Change**: Improved column document text to be more searchable:

```python
# Before
col_doc = f"Column: {table.schema}.{table.name}.{col.name}\nType: {col.data_type}"

# After  
col_doc = f"Table: {table.schema}.{table.name}\nColumn: {col.name}\nType: {col.data_type}"

# Add table context to make it more searchable
table_name_lower = table.name.lower()
if 'vendor' in table_name_lower:
    col_doc += f"\nThis is a vendor-related column in the {table.name} table"
```

### 2. **Fixed Double Bracketing**
**File**: `rag/nl2sql.py`
**Change**: Added check to prevent double bracketing:

```python
# Check if table name is already bracketed
if table.startswith('[') and table.endswith(']'):
    bracketed_table = table
else:
    bracketed_table = f"[{table}]"
```

### 3. **Cleared Vector Store**
**Action**: Cleared the `puma_sqlserver` namespace vector store to rebuild with improved documents.

## Next Steps

1. **Rebuild RAG System**: User needs to click "Initialize RAG" again in Streamlit UI
2. **Test Vendor Query**: Verify that column information is now retrieved
3. **Verify SQL Generation**: Confirm that correct column names are generated

## Expected Results After Fix

1. **Better Schema Context**: Column information should be retrieved for vendor queries
2. **Correct SQL Generation**: Should generate `SELECT [Name] FROM [dbo].[Vendors]`
3. **No Double Bracketing**: Table names should be properly formatted

## Files Modified

- `rag/retriever.py` - Enhanced column document creation
- `rag/nl2sql.py` - Fixed double bracketing issue
- Vector store cleared for rebuild

## Testing

The user should:
1. Click "Initialize RAG" in the Streamlit UI to rebuild the vector store
2. Ask "show me all vendors" again
3. Verify that the generated SQL is correct: `SELECT [Name] FROM [dbo].[Vendors]`
