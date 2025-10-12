"""
Puma Database Configuration Template

Copy this file to puma_config.py and update with your actual database details.
"""

from adapters.database_adapter import ConnectionConfig

# PUMA DATABASE CONFIGURATION
# Update these values with your actual Puma database details

PUMA_CONFIG = ConnectionConfig(
    # Database server details
    host="your-sql-server-host",        # e.g., "localhost", "192.168.1.100", "server.company.com"
    port=1433,                          # Usually 1433 for SQL Server
    database="PumaProcurement",         # Your actual Puma database name
    
    # Authentication (choose one)
    # Option 1: Windows Authentication (recommended)
    username="",                        # Leave empty for Windows Auth
    password="",                        # Leave empty for Windows Auth
    
    # Option 2: SQL Server Authentication
    # username="your-sql-username",     # Uncomment and set your SQL username
    # password="your-sql-password",     # Uncomment and set your SQL password
    
    # ODBC Driver (adjust based on what's installed on your system)
    driver="ODBC Driver 17 for SQL Server",  # Most common
    # driver="ODBC Driver 13 for SQL Server",  # Alternative
    # driver="SQL Server Native Client 11.0",  # Alternative
    
    # Connection settings
    connection_timeout=30,              # Connection timeout in seconds
    pool_size=10,                       # Connection pool size
    max_overflow=20                      # Max overflow connections
)

# SAMPLE QUERIES FOR TESTING
# Update these with your actual table names and business logic

SAMPLE_QUERIES = [
    {
        'name': 'Vendor Count',
        'sql': 'SELECT COUNT(*) as vendor_count FROM Vendors',
        'description': 'Total number of vendors'
    },
    {
        'name': 'Active Purchase Orders',
        'sql': 'SELECT COUNT(*) as active_orders FROM PurchaseOrders WHERE Status = \'Active\'',
        'description': 'Number of active purchase orders'
    },
    {
        'name': 'Recent Orders',
        'sql': '''
        SELECT TOP 10 
            po.OrderNumber,
            v.VendorName,
            po.OrderDate,
            po.TotalAmount
        FROM PurchaseOrders po
        JOIN Vendors v ON po.VendorID = v.VendorID
        ORDER BY po.OrderDate DESC
        ''',
        'description': '10 most recent purchase orders with vendor details'
    },
    {
        'name': 'Department Spending',
        'sql': '''
        SELECT 
            d.DepartmentName,
            COUNT(po.PurchaseOrderID) as order_count,
            SUM(po.TotalAmount) as total_spent
        FROM Departments d
        LEFT JOIN Employees e ON d.DepartmentID = e.DepartmentID
        LEFT JOIN PurchaseOrders po ON e.EmployeeID = po.RequesterID
        GROUP BY d.DepartmentName
        ORDER BY total_spent DESC
        ''',
        'description': 'Spending summary by department'
    },
    {
        'name': 'Product Categories',
        'sql': '''
        SELECT 
            c.CategoryName,
            COUNT(p.ProductID) as product_count,
            AVG(p.UnitPrice) as avg_price
        FROM Categories c
        LEFT JOIN Products p ON c.CategoryID = p.CategoryID
        GROUP BY c.CategoryName
        ORDER BY product_count DESC
        ''',
        'description': 'Product distribution by category'
    }
]

# BUSINESS DOMAIN MAPPING
# Map your actual table names to business domains for better analysis

BUSINESS_DOMAIN_MAPPING = {
    'procurement': [
        'Vendors', 'VendorContacts', 'VendorProducts',
        'PurchaseOrders', 'PurchaseOrderItems', 'PurchaseRequisitions',
        'Approvals', 'Contracts', 'Agreements'
    ],
    'hr': [
        'Employees', 'Departments', 'Positions', 'EmployeeRoles',
        'Payroll', 'Benefits', 'TimeTracking', 'PerformanceReviews'
    ],
    'finance': [
        'Accounts', 'Transactions', 'Invoices', 'Payments',
        'Budgets', 'CostCenters', 'FinancialReports', 'Taxes'
    ],
    'inventory': [
        'Products', 'Categories', 'Inventory', 'StockMovements',
        'Warehouses', 'Locations', 'Suppliers', 'StockLevels'
    ],
    'logistics': [
        'Shipments', 'Deliveries', 'Routes', 'Carriers',
        'Tracking', 'ShippingCosts', 'DeliverySchedules'
    ]
}

# TABLE RELATIONSHIP HINTS
# Help the schema introspector understand your table relationships

RELATIONSHIP_HINTS = {
    'PurchaseOrders': {
        'VendorID': 'Vendors.VendorID',
        'RequesterID': 'Employees.EmployeeID',
        'ApproverID': 'Employees.EmployeeID'
    },
    'PurchaseOrderItems': {
        'PurchaseOrderID': 'PurchaseOrders.PurchaseOrderID',
        'ProductID': 'Products.ProductID'
    },
    'Employees': {
        'DepartmentID': 'Departments.DepartmentID',
        'ManagerID': 'Employees.EmployeeID'
    },
    'Products': {
        'CategoryID': 'Categories.CategoryID',
        'VendorID': 'Vendors.VendorID'
    }
}

# PERFORMANCE TESTING QUERIES
# Queries to test database performance

PERFORMANCE_QUERIES = [
    {
        'name': 'Simple Count',
        'sql': 'SELECT COUNT(*) FROM Vendors',
        'expected_time': 0.1,
        'description': 'Simple count query'
    },
    {
        'name': 'Complex Join',
        'sql': '''
        SELECT 
            v.VendorName,
            COUNT(po.PurchaseOrderID) as order_count,
            SUM(po.TotalAmount) as total_spent
        FROM Vendors v
        LEFT JOIN PurchaseOrders po ON v.VendorID = po.VendorID
        GROUP BY v.VendorName
        ORDER BY total_spent DESC
        ''',
        'expected_time': 0.5,
        'description': 'Complex join with aggregation'
    },
    {
        'name': 'Date Range Query',
        'sql': '''
        SELECT COUNT(*) 
        FROM PurchaseOrders 
        WHERE OrderDate BETWEEN '2024-01-01' AND '2024-12-31'
        ''',
        'expected_time': 0.2,
        'description': 'Date range filtering'
    }
]

# NL→SQL TESTING SCENARIOS (Future Implementation)
# Natural language queries that should be converted to SQL

NL_SQL_SCENARIOS = [
    {
        'natural_language': 'Show me all vendors with pending purchase orders',
        'expected_sql': '''
        SELECT DISTINCT v.* 
        FROM Vendors v 
        JOIN PurchaseOrders po ON v.VendorID = po.VendorID 
        WHERE po.Status = 'Pending'
        ''',
        'description': 'Find vendors with pending orders'
    },
    {
        'natural_language': 'What is the total amount spent per department this month?',
        'expected_sql': '''
        SELECT 
            d.DepartmentName,
            SUM(po.TotalAmount) as total_spent
        FROM Departments d
        JOIN Employees e ON d.DepartmentID = e.DepartmentID
        JOIN PurchaseOrders po ON e.EmployeeID = po.RequesterID
        WHERE MONTH(po.OrderDate) = MONTH(GETDATE())
        AND YEAR(po.OrderDate) = YEAR(GETDATE())
        GROUP BY d.DepartmentName
        ORDER BY total_spent DESC
        ''',
        'description': 'Department spending for current month'
    },
    {
        'natural_language': 'Which products are running low on stock?',
        'expected_sql': '''
        SELECT 
            p.ProductName,
            p.CurrentStock,
            p.MinimumStock
        FROM Products p
        WHERE p.CurrentStock <= p.MinimumStock
        ORDER BY (p.CurrentStock - p.MinimumStock) ASC
        ''',
        'description': 'Find products with low stock'
    },
    {
        'natural_language': 'Show me the top 5 vendors by total purchase amount',
        'expected_sql': '''
        SELECT TOP 5
            v.VendorName,
            SUM(po.TotalAmount) as total_purchased
        FROM Vendors v
        JOIN PurchaseOrders po ON v.VendorID = po.VendorID
        GROUP BY v.VendorName
        ORDER BY total_purchased DESC
        ''',
        'description': 'Top vendors by purchase volume'
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

def get_relationship_hints():
    """Get relationship hints."""
    return RELATIONSHIP_HINTS

def get_performance_queries():
    """Get performance testing queries."""
    return PERFORMANCE_QUERIES

def get_nl_sql_scenarios():
    """Get NL→SQL testing scenarios."""
    return NL_SQL_SCENARIOS
