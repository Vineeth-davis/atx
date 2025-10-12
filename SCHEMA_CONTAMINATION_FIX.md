# Schema Contamination Fix Summary

## Problem Identified
The NL→SQL generator was mixing tables from different schemas, specifically:
- **Puma SQL Server tables**: `dbo.Vendors`, `dbo.PurchaseOrders` (correct)
- **Demo PostgreSQL tables**: `financial_income`, `entities` (incorrect contamination)

This resulted in invalid SQL queries like:
```sql
SELECT v.name, v.country, fi.revenue
FROM [dbo].[[dbo].[Vendors]] v
JOIN [dbo].[financial_income] fi ON v.id = fi.vendor_id
WHERE v.type = 'Vendor';
```

## Root Causes

### 1. Hardcoded SQL Examples
The `_get_sql_examples()` method was using hardcoded demo table names (`financial_income`, `entities`) instead of dynamic examples based on the actual schema context.

### 2. Missing Namespace Filtering
The examples generation didn't filter tables by namespace, allowing demo tables to contaminate Puma queries.

### 3. Double Bracketing Issue
Table names were being double-bracketed (`[dbo].[[dbo].[Vendors]]`) due to incorrect identifier enforcement.

## Solution Implemented

### 1. Dynamic SQL Examples (`rag/nl2sql.py`)
```python
def _get_sql_examples(self, context: List[Dict[str, Any]] = None) -> str:
    """Get example SQL queries for common patterns based on actual schema context"""
    
    # Extract table names from context
    tables = {}
    for item in context:
        if item.get('type') == 'table':
            table_name = item.get('table', '')
            namespace = item.get('namespace', '')
            # Only use tables from the correct namespace
            if table_name and namespace == self.namespace:
                tables[table_name] = item.get('description', f'Table {table_name}')
```

### 2. Namespace-Aware Filtering
- Only uses tables from the correct namespace (`puma_sqlserver` for Puma queries)
- Filters out tables from other namespaces (`atrean_demo` for demo data)
- Ensures schema isolation between different database connections

### 3. Fixed Double Bracketing
```python
# Check if table name is already bracketed
if table.startswith('[') and table.endswith(']'):
    bracketed_table = table
else:
    bracketed_table = f"[{table}]"

table_map[norm(qual)] = f"[{schema}].{bracketed_table}"
```

### 4. Enhanced Debugging
Added logging to track schema context and table names being used:
```python
logger.info(f"Schema context for namespace '{self.namespace}': {len(context)} items")
table_names = [item.get('table', '') for item in context if item.get('type') == 'table']
logger.info(f"Tables in context: {table_names}")
```

## Results

### Before Fix
```sql
SELECT v.name, v.country, fi.revenue
FROM [dbo].[[dbo].[Vendors]] v
JOIN [dbo].[financial_income] fi ON v.id = fi.vendor_id
WHERE v.type = 'Vendor';
```
**Issues**: 
- ❌ Mixed schemas (Puma + Demo)
- ❌ Double bracketing
- ❌ Non-existent table `financial_income`

### After Fix
```sql
SELECT v.name, v.country, v.contact_info
FROM [dbo].[Vendors] v
WHERE v.type = 'Vendor';
```
**Improvements**:
- ✅ Only Puma tables used
- ✅ Correct bracketing
- ✅ Valid table references

## Testing Verified
- ✅ **Namespace Filtering**: Demo tables filtered out from Puma context
- ✅ **Dynamic Examples**: Examples use actual schema tables
- ✅ **No Contamination**: No mixing of different database schemas
- ✅ **Correct Bracketing**: Single-level bracketing for SQL Server

## Impact
- **Fixed**: Schema contamination between Puma and demo data
- **Improved**: SQL examples now use actual schema tables
- **Enhanced**: Better namespace isolation
- **Robust**: Works for any database schema without hardcoded references

## Files Modified
- `rag/nl2sql.py` - Dynamic examples generation and namespace filtering
- Enhanced identifier enforcement to prevent double bracketing

The fix ensures that each database connection (Puma SQL Server, Atrean Demo) maintains its own isolated schema context, preventing cross-contamination and generating valid SQL queries using only the correct tables and columns.
