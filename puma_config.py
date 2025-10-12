"""
Puma Database Configuration - Customized for Your Database

This configuration is customized based on your actual Puma database connection details.
"""

from adapters.database_adapter import ConnectionConfig

# PUMA DATABASE CONFIGURATION
# Based on your actual connection details from app.settings

PUMA_CONFIG = ConnectionConfig(
    # Database server details from your connection string
    host="98.70.24.81",                    # Your SQL Server IP
    port=1433,                             # Default SQL Server port
    database="puma_test",                  # Your actual database name
    
    # Authentication from your connection string
    username="vineeth",                    # Your SQL Server username
    password="Fish4Lake$9",               # Your SQL Server password
    
    # ODBC Driver (will be detected automatically)
    driver="ODBC Driver 17 for SQL Server",  # Most common driver
    
    # Connection settings optimized for your setup
    connection_timeout=30,                 # Connection timeout in seconds
    pool_size=10,                          # Connection pool size
    max_overflow=20,                       # Max overflow connections
    ssl_mode=None                          # No SSL mode (will use TrustServerCertificate=true)
)

# SAMPLE QUERIES FOR PUMA TEST DATABASE
# These queries are designed to work with typical procurement database structure

SAMPLE_QUERIES = [
    {
        'name': 'Database Info',
        'sql': 'SELECT DB_NAME() as database_name, @@VERSION as sql_version',
        'description': 'Get database name and SQL Server version'
    },
    {
        'name': 'Table Count',
        'sql': 'SELECT COUNT(*) as table_count FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = \'BASE TABLE\'',
        'description': 'Count of base tables in database'
    },
    {
        'name': 'All Tables',
        'sql': 'SELECT TABLE_NAME, TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = \'BASE TABLE\' ORDER BY TABLE_NAME',
        'description': 'List all tables in the database'
    },
    {
        'name': 'Column Count',
        'sql': 'SELECT COUNT(*) as column_count FROM INFORMATION_SCHEMA.COLUMNS',
        'description': 'Count of columns across all tables'
    },
    {
        'name': 'Schema List',
        'sql': 'SELECT DISTINCT TABLE_SCHEMA as schema_name FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_SCHEMA',
        'description': 'List of schemas in database'
    },
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
        'description': 'List all indexes in the database'
    }
]

# BUSINESS DOMAIN MAPPING FOR PUMA TEST DATABASE
# This will be updated based on actual table discovery

BUSINESS_DOMAIN_MAPPING = {
    'procurement': [
        'Vendors', 'VendorContacts', 'VendorProducts',
        'PurchaseOrders', 'PurchaseOrderItems', 'PurchaseRequisitions',
        'Approvals', 'Contracts', 'Agreements', 'PurchaseRequests'
    ],
    'hr': [
        'Employees', 'Departments', 'Positions', 'EmployeeRoles',
        'Payroll', 'Benefits', 'TimeTracking', 'PerformanceReviews',
        'Users', 'UserRoles', 'UserDepartments'
    ],
    'finance': [
        'Accounts', 'Transactions', 'Invoices', 'Payments',
        'Budgets', 'CostCenters', 'FinancialReports', 'Taxes',
        'Expenses', 'Reimbursements', 'FinancialPeriods'
    ],
    'inventory': [
        'Products', 'Categories', 'Inventory', 'StockMovements',
        'Warehouses', 'Locations', 'Suppliers', 'StockLevels',
        'ProductCategories', 'InventoryItems'
    ],
    'logistics': [
        'Shipments', 'Deliveries', 'Routes', 'Carriers',
        'Tracking', 'ShippingCosts', 'DeliverySchedules',
        'ShippingMethods', 'DeliveryAddresses'
    ],
    'general': [
        'Settings', 'Configuration', 'Logs', 'AuditTrails',
        'SystemSettings', 'UserPreferences', 'Notifications'
    ]
}

# PERFORMANCE TESTING QUERIES
# Optimized for your database structure

PERFORMANCE_QUERIES = [
    {
        'name': 'Simple Count',
        'sql': 'SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES',
        'expected_time': 0.1,
        'description': 'Simple count query'
    },
    {
        'name': 'Complex Schema Query',
        'sql': '''
        SELECT 
            t.TABLE_NAME,
            COUNT(c.COLUMN_NAME) as column_count,
            COUNT(CASE WHEN c.IS_NULLABLE = 'YES' THEN 1 END) as nullable_columns
        FROM INFORMATION_SCHEMA.TABLES t
        LEFT JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME
        WHERE t.TABLE_TYPE = 'BASE TABLE'
        GROUP BY t.TABLE_NAME
        ORDER BY column_count DESC
        ''',
        'expected_time': 0.5,
        'description': 'Complex schema analysis query'
    },
    {
        'name': 'Relationship Analysis',
        'sql': '''
        SELECT 
            tc.TABLE_NAME,
            COUNT(kcu.COLUMN_NAME) as foreign_key_count
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu 
            ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
        WHERE tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
        GROUP BY tc.TABLE_NAME
        ORDER BY foreign_key_count DESC
        ''',
        'expected_time': 0.3,
        'description': 'Foreign key relationship analysis'
    }
]

# NL→SQL TESTING SCENARIOS (Future Implementation)
# Based on typical procurement database queries

NL_SQL_SCENARIOS = [
    {
        'natural_language': 'Show me all tables in the database',
        'expected_sql': 'SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = \'BASE TABLE\' ORDER BY TABLE_NAME',
        'description': 'List all database tables'
    },
    {
        'natural_language': 'What are the foreign key relationships?',
        'expected_sql': '''
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
        'description': 'Find all foreign key relationships'
    },
    {
        'natural_language': 'Which tables have the most columns?',
        'expected_sql': '''
        SELECT 
            TABLE_NAME,
            COUNT(COLUMN_NAME) as column_count
        FROM INFORMATION_SCHEMA.COLUMNS
        GROUP BY TABLE_NAME
        ORDER BY column_count DESC
        ''',
        'description': 'Find tables with most columns'
    }
]

# EXPORT CONFIGURATION
def get_config():
    """Get the database configuration."""
    return PUMA_CONFIG

def get_sample_queries():
    """Get sample queries for testing."""
    return SAMPLE_QUERIES

def get_business_domain_mapping():
    """Get business domain mapping."""
    return BUSINESS_DOMAIN_MAPPING

def get_performance_queries():
    """Get performance testing queries."""
    return PERFORMANCE_QUERIES

def get_nl_sql_scenarios():
    """Get NL→SQL testing scenarios."""
    return NL_SQL_SCENARIOS
