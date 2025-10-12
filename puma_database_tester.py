"""
Puma Database Testing Script

This script provides comprehensive testing capabilities for the Puma procurement database
using the Global RAG Platform's database adapter framework.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add current directory to Python path
sys.path.append('.')

from adapters.sqlserver_adapter import SQLServerAdapter
from adapters.database_adapter import ConnectionConfig, DatabaseType
from core.schema_introspector import get_schema_introspector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PumaDatabaseTester:
    """
    Comprehensive testing class for Puma database functionality.
    
    Features:
    - Connection testing
    - Schema introspection
    - Query execution
    - Performance analysis
    - Error handling
    """
    
    def __init__(self, config: ConnectionConfig):
        """Initialize tester with database configuration."""
        self.config = config
        self.adapter = SQLServerAdapter(config)
        self.introspector = get_schema_introspector()
        self.test_results = {}
    
    async def test_connection(self) -> bool:
        """
        Test basic database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        print("🔌 Testing database connection...")
        
        try:
            success = await self.adapter.connect()
            if success:
                print("✅ Connection successful!")
                self.test_results['connection'] = True
                return True
            else:
                print("❌ Connection failed")
                self.test_results['connection'] = False
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            self.test_results['connection'] = False
            return False
    
    async def test_basic_queries(self) -> Dict[str, Any]:
        """
        Test basic SQL queries.
        
        Returns:
            Dict: Test results
        """
        print("\n🔍 Testing basic queries...")
        
        basic_queries = [
            {
                'name': 'Table Count',
                'sql': 'SELECT COUNT(*) as table_count FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = \'BASE TABLE\'',
                'description': 'Count of base tables in database'
            },
            {
                'name': 'Column Count',
                'sql': 'SELECT COUNT(*) as column_count FROM INFORMATION_SCHEMA.COLUMNS',
                'description': 'Count of columns across all tables'
            },
            {
                'name': 'Database Info',
                'sql': 'SELECT DB_NAME() as database_name, @@VERSION as sql_version',
                'description': 'Database name and SQL Server version'
            },
            {
                'name': 'Schema List',
                'sql': 'SELECT DISTINCT TABLE_SCHEMA as schema_name FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_SCHEMA',
                'description': 'List of schemas in database'
            }
        ]
        
        results = {}
        
        for query_info in basic_queries:
            try:
                print(f"  🔍 {query_info['name']}: {query_info['description']}")
                result = await self.adapter.execute_query(query_info['sql'])
                
                results[query_info['name']] = {
                    'success': True,
                    'row_count': result.row_count,
                    'execution_time': result.execution_time,
                    'data': result.data
                }
                
                print(f"    ✅ Success: {result.row_count} rows, {result.execution_time:.3f}s")
                
                # Show sample data
                if result.data:
                    for row in result.data[:2]:  # Show first 2 rows
                        print(f"    📊 {row}")
                        
            except Exception as e:
                print(f"    ❌ Failed: {e}")
                results[query_info['name']] = {
                    'success': False,
                    'error': str(e)
                }
        
        self.test_results['basic_queries'] = results
        return results
    
    async def test_schema_introspection(self) -> Dict[str, Any]:
        """
        Test comprehensive schema introspection.
        
        Returns:
            Dict: Schema analysis results
        """
        print("\n🔍 Testing schema introspection...")
        
        try:
            analysis = await self.introspector.analyze_schema(self.adapter)
            
            results = {
                'success': True,
                'database_name': analysis.database_name,
                'total_tables': analysis.total_tables,
                'total_columns': analysis.total_columns,
                'total_relationships': analysis.total_relationships,
                'business_domains': analysis.business_domains,
                'data_quality_score': analysis.data_quality_score,
                'complexity_score': analysis.complexity_score,
                'relationships': analysis.relationships,
                'table_clusters': analysis.table_clusters
            }
            
            print(f"✅ Schema analysis completed:")
            print(f"  🗄️  Database: {analysis.database_name}")
            print(f"  📊 Tables: {analysis.total_tables}")
            print(f"  📊 Columns: {analysis.total_columns}")
            print(f"  🔗 Relationships: {analysis.total_relationships}")
            print(f"  🎯 Business Domains: {len(analysis.business_domains)}")
            print(f"  📈 Data Quality: {analysis.data_quality_score:.2f}/1.0")
            print(f"  🧮 Complexity: {analysis.complexity_score:.2f}/1.0")
            
            # Show business domains
            if analysis.business_domains:
                print(f"\n🎯 Detected Business Domains:")
                for domain, tables in analysis.business_domains.items():
                    print(f"  📊 {domain.value.upper()}: {', '.join(tables)}")
            
            # Show key relationships
            if analysis.relationships:
                print(f"\n🔗 Key Relationships:")
                for i, rel in enumerate(analysis.relationships[:5], 1):
                    print(f"  {i}. {rel.source_table} → {rel.target_table} ({rel.relationship_type.value})")
            
            self.test_results['schema_introspection'] = results
            return results
            
        except Exception as e:
            print(f"❌ Schema introspection failed: {e}")
            results = {'success': False, 'error': str(e)}
            self.test_results['schema_introspection'] = results
            return results
    
    async def test_custom_queries(self, custom_queries: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Test custom SQL queries.
        
        Args:
            custom_queries: List of query dictionaries with 'name', 'sql', 'description'
            
        Returns:
            Dict: Test results
        """
        print(f"\n🔍 Testing {len(custom_queries)} custom queries...")
        
        results = {}
        
        for query_info in custom_queries:
            try:
                print(f"  🔍 {query_info['name']}: {query_info['description']}")
                result = await self.adapter.execute_query(query_info['sql'])
                
                results[query_info['name']] = {
                    'success': True,
                    'row_count': result.row_count,
                    'execution_time': result.execution_time,
                    'data': result.data[:10] if result.data else []  # Limit to 10 rows
                }
                
                print(f"    ✅ Success: {result.row_count} rows, {result.execution_time:.3f}s")
                
                # Show sample data
                if result.data:
                    print(f"    📊 Sample data:")
                    for row in result.data[:3]:  # Show first 3 rows
                        print(f"      {row}")
                        
            except Exception as e:
                print(f"    ❌ Failed: {e}")
                results[query_info['name']] = {
                    'success': False,
                    'error': str(e)
                }
        
        self.test_results['custom_queries'] = results
        return results
    
    async def test_performance(self) -> Dict[str, Any]:
        """
        Test database performance metrics.
        
        Returns:
            Dict: Performance test results
        """
        print("\n⚡ Testing performance...")
        
        performance_queries = [
            {
                'name': 'Simple Count',
                'sql': 'SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES',
                'expected_time': 0.1
            },
            {
                'name': 'Complex Join',
                'sql': '''
                SELECT 
                    t.TABLE_NAME,
                    COUNT(c.COLUMN_NAME) as column_count
                FROM INFORMATION_SCHEMA.TABLES t
                LEFT JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME
                GROUP BY t.TABLE_NAME
                ORDER BY column_count DESC
                ''',
                'expected_time': 0.5
            }
        ]
        
        results = {}
        
        for query_info in performance_queries:
            try:
                start_time = datetime.now()
                result = await self.adapter.execute_query(query_info['sql'])
                end_time = datetime.now()
                
                execution_time = (end_time - start_time).total_seconds()
                
                results[query_info['name']] = {
                    'success': True,
                    'execution_time': execution_time,
                    'expected_time': query_info['expected_time'],
                    'performance_ratio': execution_time / query_info['expected_time'],
                    'row_count': result.row_count
                }
                
                status = "✅ Good" if execution_time <= query_info['expected_time'] else "⚠️ Slow"
                print(f"  {status} {query_info['name']}: {execution_time:.3f}s (expected: {query_info['expected_time']}s)")
                
            except Exception as e:
                print(f"  ❌ {query_info['name']} failed: {e}")
                results[query_info['name']] = {
                    'success': False,
                    'error': str(e)
                }
        
        self.test_results['performance'] = results
        return results
    
    async def generate_test_report(self) -> str:
        """
        Generate comprehensive test report.
        
        Returns:
            str: Formatted test report
        """
        report = f"""
# Puma Database Test Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Connection Details
- **Host**: {self.config.host}:{self.config.port}
- **Database**: {self.config.database}
- **Driver**: {self.config.driver}
- **Authentication**: {'Windows Auth' if not self.config.username else 'SQL Auth'}

## Test Results Summary
"""
        
        # Connection test
        if 'connection' in self.test_results:
            status = "✅ PASSED" if self.test_results['connection'] else "❌ FAILED"
            report += f"- **Connection Test**: {status}\n"
        
        # Basic queries
        if 'basic_queries' in self.test_results:
            passed = sum(1 for q in self.test_results['basic_queries'].values() if q.get('success', False))
            total = len(self.test_results['basic_queries'])
            report += f"- **Basic Queries**: {passed}/{total} passed\n"
        
        # Schema introspection
        if 'schema_introspection' in self.test_results:
            if self.test_results['schema_introspection'].get('success', False):
                si = self.test_results['schema_introspection']
                report += f"- **Schema Introspection**: ✅ PASSED\n"
                report += f"  - Tables: {si['total_tables']}\n"
                report += f"  - Columns: {si['total_columns']}\n"
                report += f"  - Relationships: {si['total_relationships']}\n"
                report += f"  - Data Quality: {si['data_quality_score']:.2f}/1.0\n"
                report += f"  - Complexity: {si['complexity_score']:.2f}/1.0\n"
            else:
                report += f"- **Schema Introspection**: ❌ FAILED\n"
        
        # Custom queries
        if 'custom_queries' in self.test_results:
            passed = sum(1 for q in self.test_results['custom_queries'].values() if q.get('success', False))
            total = len(self.test_results['custom_queries'])
            report += f"- **Custom Queries**: {passed}/{total} passed\n"
        
        # Performance
        if 'performance' in self.test_results:
            passed = sum(1 for q in self.test_results['performance'].values() if q.get('success', False))
            total = len(self.test_results['performance'])
            report += f"- **Performance Tests**: {passed}/{total} passed\n"
        
        report += "\n## Recommendations\n"
        
        if 'schema_introspection' in self.test_results and self.test_results['schema_introspection'].get('success', False):
            si = self.test_results['schema_introspection']
            if si['data_quality_score'] < 0.7:
                report += "- Consider improving data quality by adding more indexes and foreign key constraints\n"
            if si['complexity_score'] > 0.7:
                report += "- Schema complexity is high, consider normalization\n"
        
        report += "- Ready for NL→SQL implementation (Phase 3)\n"
        report += "- Consider implementing business-specific query patterns\n"
        
        return report
    
    async def disconnect(self):
        """Disconnect from database."""
        try:
            await self.adapter.disconnect()
            print("🔌 Disconnected from database")
        except Exception as e:
            print(f"⚠️ Error during disconnect: {e}")


async def main():
    """Main testing function."""
    
    print("🚀 Puma Database Testing Suite")
    print("=" * 50)
    
    # Configure your database connection here
    config = ConnectionConfig(
        host="your-sql-server-host",        # Replace with your SQL Server host
        port=1433,                          # Usually 1433
        database="PumaProcurement",         # Replace with your database name
        username="your-username",           # Replace with your username (empty for Windows Auth)
        password="your-password",           # Replace with your password (empty for Windows Auth)
        driver="ODBC Driver 17 for SQL Server"  # Adjust driver name if needed
    )
    
    # Create tester instance
    tester = PumaDatabaseTester(config)
    
    try:
        # Test connection
        if not await tester.test_connection():
            print("❌ Cannot proceed without database connection")
            return
        
        # Run all tests
        await tester.test_basic_queries()
        await tester.test_schema_introspection()
        await tester.test_performance()
        
        # Test custom queries (add your specific queries here)
        custom_queries = [
            {
                'name': 'Vendor Count',
                'sql': 'SELECT COUNT(*) as vendor_count FROM Vendors',  # Adjust table name
                'description': 'Count of vendors in database'
            },
            {
                'name': 'Purchase Orders',
                'sql': 'SELECT TOP 5 * FROM PurchaseOrders ORDER BY OrderDate DESC',  # Adjust table name
                'description': 'Recent purchase orders'
            }
            # Add more custom queries based on your schema
        ]
        
        await tester.test_custom_queries(custom_queries)
        
        # Generate report
        report = await tester.generate_test_report()
        print("\n" + "=" * 50)
        print(report)
        
        # Save report to file
        with open('puma_test_report.md', 'w') as f:
            f.write(report)
        print("\n📄 Test report saved to 'puma_test_report.md'")
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        logger.exception("Testing error")
    
    finally:
        await tester.disconnect()


if __name__ == "__main__":
    print("""
🔧 PUMA DATABASE TESTING SCRIPT

Before running this script, please:

1. Update the connection configuration in the main() function:
   - host: Your SQL Server hostname/IP
   - database: Your Puma database name
   - username/password: Your credentials (or leave empty for Windows Auth)
   - driver: Your ODBC driver name

2. Update the custom queries section with your actual table names

3. Install required packages:
   pip install pyodbc

4. Run the script:
   python puma_database_tester.py

This will test:
✅ Database connection
✅ Basic SQL queries
✅ Schema introspection
✅ Performance metrics
✅ Custom queries
✅ Generate comprehensive report
""")
    
    # Uncomment the line below to run the tests
    # asyncio.run(main())
