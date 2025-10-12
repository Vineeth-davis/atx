# Puma Database Testing Guide

## 🎯 **Overview**

This guide shows you how to test the Global RAG Platform's database functionality with a real Puma procurement database. We'll cover schema introspection, connection testing, and prepare for NL→SQL testing.

## 📋 **What Can Be Tested Right Now**

### ✅ **Currently Available for Testing:**

1. **Database Connection Testing**
   - SQL Server connection establishment
   - Connection pooling
   - Authentication (Windows Auth & SQL Auth)
   - SSL/TLS connectivity

2. **Schema Introspection**
   - Complete schema discovery
   - Business domain detection
   - Relationship analysis
   - Data quality assessment
   - Table clustering
   - Documentation generation

3. **Database Adapter Framework**
   - Query execution
   - Schema retrieval
   - Connection management
   - Error handling

### 🚧 **Not Yet Available (Requires Additional Implementation):**

1. **Natural Language to SQL (NL→SQL)**
   - Requires Phase 3: Enhanced Agent System
   - Needs Universal Schema Retriever
   - Needs Adaptive SQL Generator

2. **Advanced SQL Features**
   - Complex joins across tables
   - CTEs and window functions
   - Business logic integration

## 🔧 **Prerequisites for Testing**

### **1. Puma Database Access**
You need access to a Puma procurement database with:
- **Server**: SQL Server instance
- **Database**: Puma procurement database
- **Authentication**: Windows Auth or SQL Auth credentials
- **Network**: Accessible from your development machine

### **2. Required Python Packages**
```bash
pip install pyodbc>=5.0.0
pip install asyncio
pip install dataclasses
pip install typing
```

### **3. SQL Server ODBC Driver**
Ensure you have one of these installed:
- **ODBC Driver 17 for SQL Server** (recommended)
- **ODBC Driver 13 for SQL Server**
- **SQL Server Native Client**

## 🚀 **Testing Scenarios**

### **Scenario 1: Basic Connection Test**

Create a simple connection test script:

```python
# test_puma_connection.py
import asyncio
import sys
sys.path.append('.')

from adapters.sqlserver_adapter import SQLServerAdapter
from adapters.database_adapter import ConnectionConfig, DatabaseType

async def test_puma_connection():
    """Test basic connection to Puma database."""
    
    # Configure connection (replace with your actual values)
    config = ConnectionConfig(
        host="your-sql-server-host",  # e.g., "localhost" or "server.domain.com"
        port=1433,
        database="PumaProcurement",  # Replace with actual database name
        username="your-username",    # Leave empty for Windows Auth
        password="your-password",    # Leave empty for Windows Auth
        driver="ODBC Driver 17 for SQL Server"
    )
    
    adapter = SQLServerAdapter(config)
    
    try:
        print("🔌 Testing connection to Puma database...")
        success = await adapter.connect()
        
        if success:
            print("✅ Connection successful!")
            
            # Test basic query
            result = await adapter.execute_query("SELECT COUNT(*) as table_count FROM INFORMATION_SCHEMA.TABLES")
            print(f"📊 Database has {result.data[0]['table_count']} tables")
            
            await adapter.disconnect()
            print("🔌 Connection closed")
        else:
            print("❌ Connection failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_puma_connection())
```

### **Scenario 2: Schema Introspection Test**

```python
# test_puma_schema.py
import asyncio
import sys
sys.path.append('.')

from adapters.sqlserver_adapter import SQLServerAdapter
from adapters.database_adapter import ConnectionConfig
from core.schema_introspector import get_schema_introspector

async def test_puma_schema():
    """Test schema introspection on Puma database."""
    
    config = ConnectionConfig(
        host="your-sql-server-host",
        port=1433,
        database="PumaProcurement",
        username="your-username",
        password="your-password",
        driver="ODBC Driver 17 for SQL Server"
    )
    
    adapter = SQLServerAdapter(config)
    introspector = get_schema_introspector()
    
    try:
        print("🔌 Connecting to Puma database...")
        await adapter.connect()
        
        print("🔍 Analyzing schema...")
        analysis = await introspector.analyze_schema(adapter)
        
        print(f"\n📊 Schema Analysis Results:")
        print(f"  🗄️  Database: {analysis.database_name}")
        print(f"  📊 Tables: {analysis.total_tables}")
        print(f"  📊 Columns: {analysis.total_columns}")
        print(f"  🔗 Relationships: {analysis.total_relationships}")
        print(f"  🎯 Business Domains: {len(analysis.business_domains)}")
        print(f"  📈 Data Quality: {analysis.data_quality_score:.2f}/1.0")
        print(f"  🧮 Complexity: {analysis.complexity_score:.2f}/1.0")
        
        print(f"\n🎯 Detected Business Domains:")
        for domain, tables in analysis.business_domains.items():
            print(f"  📊 {domain.value.upper()}: {', '.join(tables)}")
        
        print(f"\n🔗 Key Relationships:")
        for i, rel in enumerate(analysis.relationships[:5], 1):  # Show first 5
            print(f"  {i}. {rel.source_table} → {rel.target_table} ({rel.relationship_type.value})")
        
        await adapter.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_puma_schema())
```

### **Scenario 3: Query Execution Test**

```python
# test_puma_queries.py
import asyncio
import sys
sys.path.append('.')

from adapters.sqlserver_adapter import SQLServerAdapter
from adapters.database_adapter import ConnectionConfig

async def test_puma_queries():
    """Test various SQL queries on Puma database."""
    
    config = ConnectionConfig(
        host="your-sql-server-host",
        port=1433,
        database="PumaProcurement",
        username="your-username",
        password="your-password",
        driver="ODBC Driver 17 for SQL Server"
    )
    
    adapter = SQLServerAdapter(config)
    
    # Test queries (adjust table names based on your schema)
    test_queries = [
        "SELECT TOP 5 * FROM INFORMATION_SCHEMA.TABLES",
        "SELECT COUNT(*) as total_tables FROM INFORMATION_SCHEMA.TABLES",
        "SELECT TOP 10 * FROM INFORMATION_SCHEMA.COLUMNS",
        # Add your actual table queries here:
        # "SELECT TOP 5 * FROM Vendors",
        # "SELECT COUNT(*) FROM PurchaseOrders",
        # "SELECT TOP 5 * FROM Products"
    ]
    
    try:
        print("🔌 Connecting to Puma database...")
        await adapter.connect()
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test Query {i}:")
            print(f"SQL: {query}")
            
            try:
                result = await adapter.execute_query(query)
                print(f"✅ Success: {result.row_count} rows returned")
                print(f"⏱️  Execution time: {result.execution_time:.3f}s")
                
                if result.data:
                    print("📊 Sample data:")
                    for row in result.data[:3]:  # Show first 3 rows
                        print(f"  {row}")
                        
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
        await adapter.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_puma_queries())
```

## 🔍 **What You Need to Provide**

### **1. Database Connection Details**
```python
# Replace these with your actual Puma database details
config = ConnectionConfig(
    host="your-sql-server-host",        # e.g., "localhost", "192.168.1.100", "server.company.com"
    port=1433,                          # Usually 1433 for SQL Server
    database="PumaProcurement",         # Your actual database name
    username="your-username",           # SQL Server username (empty for Windows Auth)
    password="your-password",           # SQL Server password (empty for Windows Auth)
    driver="ODBC Driver 17 for SQL Server"  # ODBC driver name
)
```

### **2. Sample Table Names**
Provide the actual table names from your Puma database:
- Vendor tables
- Purchase order tables
- Product tables
- Employee tables
- Department tables
- Any other relevant tables

### **3. Sample Queries**
Provide some real queries you'd like to test:
```sql
-- Examples (replace with your actual table names)
SELECT TOP 10 * FROM Vendors
SELECT COUNT(*) FROM PurchaseOrders WHERE Status = 'Approved'
SELECT v.VendorName, COUNT(po.PurchaseOrderID) as OrderCount 
FROM Vendors v 
LEFT JOIN PurchaseOrders po ON v.VendorID = po.VendorID 
GROUP BY v.VendorName
```

## 🚧 **NL→SQL Testing (Future Implementation)**

### **What's Needed for NL→SQL:**

1. **Phase 3 Implementation** (not yet done):
   - Universal Schema Retriever
   - Adaptive SQL Generator
   - Business Logic Integration

2. **Example NL→SQL Queries** (when implemented):
   ```
   Natural Language: "Show me all vendors with pending purchase orders"
   Generated SQL: SELECT v.* FROM Vendors v JOIN PurchaseOrders po ON v.VendorID = po.VendorID WHERE po.Status = 'Pending'
   
   Natural Language: "What's the total amount spent per department this month?"
   Generated SQL: SELECT d.DepartmentName, SUM(po.TotalAmount) FROM Departments d JOIN Employees e ON d.DepartmentID = e.DepartmentID JOIN PurchaseOrders po ON e.EmployeeID = po.RequesterID WHERE MONTH(po.OrderDate) = MONTH(GETDATE()) GROUP BY d.DepartmentName
   ```

## 🎯 **Testing Checklist**

### **Phase 1 Testing (Current):**
- [ ] Database connection establishment
- [ ] Schema introspection and analysis
- [ ] Business domain detection
- [ ] Relationship mapping
- [ ] Data quality assessment
- [ ] Query execution
- [ ] Error handling
- [ ] Connection pooling

### **Phase 3 Testing (Future):**
- [ ] Natural language query processing
- [ ] SQL generation accuracy
- [ ] Complex join handling
- [ ] Business logic integration
- [ ] Query optimization
- [ ] Result formatting

## 🚀 **Quick Start**

1. **Install dependencies:**
   ```bash
   pip install pyodbc asyncio
   ```

2. **Create test script:**
   ```bash
   # Copy one of the test scenarios above
   # Update connection details
   # Run the test
   python test_puma_connection.py
   ```

3. **Run schema analysis:**
   ```bash
   python test_puma_schema.py
   ```

4. **Test queries:**
   ```bash
   python test_puma_queries.py
   ```

## 📞 **Next Steps**

Once you provide the database connection details and table structure, I can:

1. **Create customized test scripts** for your specific Puma database
2. **Implement NL→SQL functionality** (Phase 3)
3. **Add business-specific query patterns**
4. **Create a web interface** for testing
5. **Integrate with your existing Puma system**

**What information do you need to provide to get started with testing?**
