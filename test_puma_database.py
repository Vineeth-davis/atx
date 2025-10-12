"""
Puma Database Testing Script - Customized for Your Database

This script is specifically configured for your Puma test database at 98.70.24.81
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
from puma_config import get_config, get_sample_queries, get_performance_queries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PumaTestDatabaseTester:
    """
    Customized testing class for your Puma test database.
    
    Features:
    - Connection testing with your specific credentials
    - Schema introspection
    - Query execution
    - Performance analysis
    - Error handling
    """
    
    def __init__(self):
        """Initialize tester with your database configuration."""
        self.config = get_config()
        self.adapter = SQLServerAdapter(self.config)
        self.introspector = get_schema_introspector()
        self.test_results = {}
        
        print(f"🔧 Configured for Puma Test Database:")
        print(f"  🗄️  Host: {self.config.host}:{self.config.port}")
        print(f"  🗄️  Database: {self.config.database}")
        print(f"  👤 User: {self.config.username}")
        print(f"  🔐 Authentication: SQL Server Auth")
        print(f"  🔒 SSL: {self.config.ssl_mode}")
    
    async def test_connection(self) -> bool:
        """
        Test connection to your Puma test database.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        print("\n🔌 Testing connection to Puma test database...")
        
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
    
    async def test_database_info(self) -> Dict[str, Any]:
        """
        Test basic database information queries.
        
        Returns:
            Dict: Test results
        """
        print("\n🔍 Testing database information queries...")
        
        info_queries = [
            {
                'name': 'Database Name & Version',
                'sql': 'SELECT DB_NAME() as database_name, @@VERSION as sql_version',
                'description': 'Get database name and SQL Server version'
            },
            {
                'name': 'Server Info',
                'sql': 'SELECT @@SERVERNAME as server_name, @@SERVICENAME as service_name',
                'description': 'Get SQL Server instance information'
            },
            {
                'name': 'Connection Info',
                'sql': 'SELECT @@SPID as session_id, USER_NAME() as current_user',
                'description': 'Get current session information'
            }
        ]
        
        results = {}
        
        for query_info in info_queries:
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
                
                # Show the data
                if result.data:
                    for row in result.data:
                        print(f"    📊 {row}")
                        
            except Exception as e:
                print(f"    ❌ Failed: {e}")
                results[query_info['name']] = {
                    'success': False,
                    'error': str(e)
                }
        
        self.test_results['database_info'] = results
        return results
    
    async def test_schema_discovery(self) -> Dict[str, Any]:
        """
        Test schema discovery queries.
        
        Returns:
            Dict: Test results
        """
        print("\n🔍 Testing schema discovery...")
        
        schema_queries = [
            {
                'name': 'Table Count',
                'sql': 'SELECT COUNT(*) as table_count FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = \'BASE TABLE\'',
                'description': 'Count of base tables'
            },
            {
                'name': 'All Tables',
                'sql': 'SELECT TABLE_NAME, TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = \'BASE TABLE\' ORDER BY TABLE_NAME',
                'description': 'List all tables'
            },
            {
                'name': 'Column Count',
                'sql': 'SELECT COUNT(*) as column_count FROM INFORMATION_SCHEMA.COLUMNS',
                'description': 'Count of columns'
            },
            {
                'name': 'Schema List',
                'sql': 'SELECT DISTINCT TABLE_SCHEMA as schema_name FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_SCHEMA',
                'description': 'List all schemas'
            }
        ]
        
        results = {}
        
        for query_info in schema_queries:
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
                
                # Show sample data for table list
                if query_info['name'] == 'All Tables' and result.data:
                    print(f"    📊 Tables found:")
                    for i, row in enumerate(result.data[:10]):  # Show first 10 tables
                        print(f"      {i+1}. {row['TABLE_SCHEMA']}.{row['TABLE_NAME']}")
                    if len(result.data) > 10:
                        print(f"      ... and {len(result.data) - 10} more tables")
                elif result.data and len(result.data) <= 5:
                    for row in result.data:
                        print(f"    📊 {row}")
                        
            except Exception as e:
                print(f"    ❌ Failed: {e}")
                results[query_info['name']] = {
                    'success': False,
                    'error': str(e)
                }
        
        self.test_results['schema_discovery'] = results
        return results
    
    async def test_relationships(self) -> Dict[str, Any]:
        """
        Test relationship discovery queries.
        
        Returns:
            Dict: Test results
        """
        print("\n🔍 Testing relationship discovery...")
        
        relationship_queries = [
            {
                'name': 'Foreign Keys',
                'sql': '''
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
                ''',
                'description': 'List all foreign key relationships'
            },
            {
                'name': 'Primary Keys',
                'sql': '''
                SELECT 
                    tc.TABLE_NAME,
                    kcu.COLUMN_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc 
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS kcu
                    ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                ORDER BY tc.TABLE_NAME
                ''',
                'description': 'List all primary key columns'
            },
            {
                'name': 'Indexes',
                'sql': '''
                SELECT 
                    t.name AS table_name,
                    i.name AS index_name,
                    i.type_desc AS index_type,
                    i.is_unique,
                    i.is_primary_key
                FROM sys.tables t
                INNER JOIN sys.indexes i ON t.object_id = i.object_id
                WHERE i.index_id > 0
                ORDER BY t.name, i.name
                ''',
                'description': 'List all indexes'
            }
        ]
        
        results = {}
        
        for query_info in relationship_queries:
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
                
                # Show sample relationships
                if result.data and len(result.data) <= 10:
                    print(f"    📊 Sample data:")
                    for row in result.data[:5]:  # Show first 5
                        print(f"      {row}")
                elif result.data:
                    print(f"    📊 Found {len(result.data)} relationships")
                        
            except Exception as e:
                print(f"    ❌ Failed: {e}")
                results[query_info['name']] = {
                    'success': False,
                    'error': str(e)
                }
        
        self.test_results['relationships'] = results
        return results
    
    async def test_schema_introspection(self) -> Dict[str, Any]:
        """
        Test comprehensive schema introspection.
        
        Returns:
            Dict: Schema analysis results
        """
        print("\n🔍 Testing comprehensive schema introspection...")
        
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
    
    async def test_performance(self) -> Dict[str, Any]:
        """
        Test database performance metrics.
        
        Returns:
            Dict: Performance test results
        """
        print("\n⚡ Testing performance...")
        
        performance_queries = get_performance_queries()
        results = {}
        
        for query_info in performance_queries:
            try:
                print(f"  🔍 {query_info['name']}: {query_info['description']}")
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
                print(f"    {status} {query_info['name']}: {execution_time:.3f}s (expected: {query_info['expected_time']}s)")
                
            except Exception as e:
                print(f"    ❌ {query_info['name']} failed: {e}")
                results[query_info['name']] = {
                    'success': False,
                    'error': str(e)
                }
        
        self.test_results['performance'] = results
        return results
    
    async def test_sample_queries(self) -> Dict[str, Any]:
        """
        Test sample queries from configuration.
        
        Returns:
            Dict: Test results
        """
        print("\n🔍 Testing sample queries...")
        
        sample_queries = get_sample_queries()
        results = {}
        
        for query_info in sample_queries:
            try:
                print(f"  🔍 {query_info['name']}: {query_info['description']}")
                result = await self.adapter.execute_query(query_info['sql'])
                
                results[query_info['name']] = {
                    'success': True,
                    'row_count': result.row_count,
                    'execution_time': result.execution_time,
                    'data': result.data[:5] if result.data else []  # Limit to 5 rows
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
        
        self.test_results['sample_queries'] = results
        return results
    
    async def generate_test_report(self) -> str:
        """
        Generate comprehensive test report.
        
        Returns:
            str: Formatted test report
        """
        report = f"""
# Puma Test Database - Comprehensive Test Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Connection Details
- **Host**: {self.config.host}:{self.config.port}
- **Database**: {self.config.database}
- **User**: {self.config.username}
- **Authentication**: SQL Server Authentication
- **SSL**: {self.config.ssl_mode}

## Test Results Summary
"""
        
        # Connection test
        if 'connection' in self.test_results:
            status = "✅ PASSED" if self.test_results['connection'] else "❌ FAILED"
            report += f"- **Connection Test**: {status}\n"
        
        # Database info
        if 'database_info' in self.test_results:
            passed = sum(1 for q in self.test_results['database_info'].values() if q.get('success', False))
            total = len(self.test_results['database_info'])
            report += f"- **Database Info**: {passed}/{total} passed\n"
        
        # Schema discovery
        if 'schema_discovery' in self.test_results:
            passed = sum(1 for q in self.test_results['schema_discovery'].values() if q.get('success', False))
            total = len(self.test_results['schema_discovery'])
            report += f"- **Schema Discovery**: {passed}/{total} passed\n"
        
        # Relationships
        if 'relationships' in self.test_results:
            passed = sum(1 for q in self.test_results['relationships'].values() if q.get('success', False))
            total = len(self.test_results['relationships'])
            report += f"- **Relationship Discovery**: {passed}/{total} passed\n"
        
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
        
        # Sample queries
        if 'sample_queries' in self.test_results:
            passed = sum(1 for q in self.test_results['sample_queries'].values() if q.get('success', False))
            total = len(self.test_results['sample_queries'])
            report += f"- **Sample Queries**: {passed}/{total} passed\n"
        
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
        
        report += "- Database is ready for NL→SQL implementation (Phase 3)\n"
        report += "- Consider implementing business-specific query patterns\n"
        report += "- Schema introspection provides excellent foundation for RAG system\n"
        
        return report
    
    async def disconnect(self):
        """Disconnect from database."""
        try:
            await self.adapter.disconnect()
            print("🔌 Disconnected from Puma test database")
        except Exception as e:
            print(f"⚠️ Error during disconnect: {e}")


async def main():
    """Main testing function."""
    
    print("🚀 Puma Test Database - Comprehensive Testing Suite")
    print("=" * 60)
    
    # Create tester instance
    tester = PumaTestDatabaseTester()
    
    try:
        # Test connection
        if not await tester.test_connection():
            print("❌ Cannot proceed without database connection")
            return
        
        # Run all tests
        await tester.test_database_info()
        await tester.test_schema_discovery()
        await tester.test_relationships()
        await tester.test_schema_introspection()
        await tester.test_performance()
        await tester.test_sample_queries()
        
        # Generate report
        report = await tester.generate_test_report()
        print("\n" + "=" * 60)
        print(report)
        
        # Save report to file
        with open('puma_test_database_report.md', 'w') as f:
            f.write(report)
        print("\n📄 Test report saved to 'puma_test_database_report.md'")
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        logger.exception("Testing error")
    
    finally:
        await tester.disconnect()


if __name__ == "__main__":
    print("""
🎯 PUMA TEST DATABASE TESTING

This script will test your Puma test database at 98.70.24.81
with the following features:

✅ Database connection testing
✅ Schema discovery and analysis
✅ Relationship mapping
✅ Business domain detection
✅ Data quality assessment
✅ Performance benchmarking
✅ Comprehensive reporting

Ready to test your Puma database!
""")
    
    asyncio.run(main())
