"""
Simple Puma Database Test

This script performs a simple test to see what's actually in your Puma database.
"""

import asyncio
import sys
import pyodbc
from datetime import datetime

# Add current directory to Python path
sys.path.append('.')

async def test_puma_simple():
    """Simple test to see what's in the Puma database."""
    
    print("🚀 Simple Puma Database Test")
    print("=" * 50)
    
    # Connection string based on your app.settings
    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=98.70.24.81,1433;"
        "DATABASE=puma_test;"
        "UID=vineeth;"
        "PWD=Fish4Lake$9;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )
    
    print(f"🔌 Connecting to: 98.70.24.81:1433/puma_test")
    
    try:
        # Test connection
        conn = pyodbc.connect(connection_string, timeout=30)
        print("✅ Connection successful!")
        
        cursor = conn.cursor()
        
        # Test basic queries
        print("\n🔍 Testing basic queries...")
        
        # Database info
        print("\n1. Database Information:")
        cursor.execute("SELECT DB_NAME() as database_name, @@VERSION as sql_version")
        for row in cursor.fetchall():
            print(f"   Database: {row[0]}")
            print(f"   Version: {row[1][:50]}...")
        
        # Table count
        print("\n2. Table Count:")
        cursor.execute("SELECT COUNT(*) as table_count FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        table_count = cursor.fetchone()[0]
        print(f"   Total Tables: {table_count}")
        
        if table_count > 0:
            # List all tables
            print("\n3. All Tables:")
            cursor.execute("SELECT TABLE_NAME, TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME")
            tables = cursor.fetchall()
            
            for i, (table_name, schema_name) in enumerate(tables, 1):
                print(f"   {i:2d}. {schema_name}.{table_name}")
            
            # Column count
            print(f"\n4. Column Count:")
            cursor.execute("SELECT COUNT(*) as column_count FROM INFORMATION_SCHEMA.COLUMNS")
            column_count = cursor.fetchone()[0]
            print(f"   Total Columns: {column_count}")
            
            # Sample table details
            if tables:
                sample_table = tables[0][0]
                print(f"\n5. Sample Table Details ({sample_table}):")
                cursor.execute(f"""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        IS_NULLABLE,
                        COLUMN_DEFAULT
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = '{sample_table}'
                    ORDER BY ORDINAL_POSITION
                """)
                
                columns = cursor.fetchall()
                for col_name, data_type, nullable, default in columns:
                    nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                    default_str = f", DEFAULT: {default}" if default else ""
                    print(f"   - {col_name}: {data_type} {nullable_str}{default_str}")
            
            # Foreign keys
            print(f"\n6. Foreign Key Relationships:")
            cursor.execute("""
                SELECT 
                    tc.TABLE_NAME,
                    kcu.COLUMN_NAME,
                    ccu.TABLE_NAME AS FOREIGN_TABLE_NAME,
                    ccu.COLUMN_NAME AS FOREIGN_COLUMN_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc 
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS kcu
                    ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE AS ccu
                    ON ccu.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
                WHERE tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
                ORDER BY tc.TABLE_NAME
            """)
            
            fks = cursor.fetchall()
            if fks:
                for table, col, fk_table, fk_col in fks:
                    print(f"   {table}.{col} -> {fk_table}.{fk_col}")
            else:
                print("   No foreign key relationships found")
            
            # Primary keys
            print(f"\n7. Primary Key Columns:")
            cursor.execute("""
                SELECT 
                    tc.TABLE_NAME,
                    kcu.COLUMN_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc 
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS kcu
                    ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                ORDER BY tc.TABLE_NAME
            """)
            
            pks = cursor.fetchall()
            if pks:
                for table, col in pks:
                    print(f"   {table}.{col}")
            else:
                print("   No primary key constraints found")
        
        else:
            print("\n⚠️  No tables found in the database!")
            print("   This might be an empty database or the user doesn't have access to view tables.")
        
        # Test a simple query
        print(f"\n8. Testing Simple Query:")
        try:
            cursor.execute("SELECT GETDATE() as current_time")
            result = cursor.fetchone()
            print(f"   Current server time: {result[0]}")
        except Exception as e:
            print(f"   Query failed: {e}")
        
        conn.close()
        print("\n✅ Test completed successfully!")
        
        # Summary
        print(f"\n📊 SUMMARY:")
        print(f"   - Connection: SUCCESS")
        print(f"   - Database: puma_test")
        print(f"   - Tables: {table_count}")
        print(f"   - Columns: {column_count if table_count > 0 else 0}")
        print(f"   - Foreign Keys: {len(fks) if table_count > 0 else 0}")
        print(f"   - Primary Keys: {len(pks) if table_count > 0 else 0}")
        
        if table_count > 0:
            print(f"\n🎯 NEXT STEPS:")
            print(f"   - Database is ready for schema introspection")
            print(f"   - Can proceed with business domain detection")
            print(f"   - Ready for NL→SQL implementation (Phase 3)")
        else:
            print(f"\n⚠️  ISSUES:")
            print(f"   - Database appears to be empty")
            print(f"   - Check if tables exist or user has proper permissions")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_puma_simple())
