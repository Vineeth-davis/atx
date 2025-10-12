"""
Schema Introspection Engine Demo

Demonstrates the comprehensive schema analysis capabilities including:
- Business domain detection
- Relationship analysis
- Table clustering
- Data quality assessment
- Schema complexity analysis
- Documentation generation
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any

# Add current directory to Python path
sys.path.append('.')

from core.schema_introspector import (
    SchemaIntrospector,
    BusinessDomain,
    RelationshipType,
    get_schema_introspector
)
from adapters.database_adapter import (
    DatabaseType,
    DatabaseSchema,
    TableInfo,
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_procurement_schema() -> DatabaseSchema:
    """Create a sample procurement database schema for demonstration."""
    
    # Vendors table
    vendors_table = TableInfo(
        name="vendors",
        schema="dbo",
        columns=[
            ColumnInfo(
                name="vendor_id",
                data_type="int",
                is_primary_key=True,
                is_nullable=False,
                description="Unique vendor identifier"
            ),
            ColumnInfo(
                name="vendor_name",
                data_type="varchar",
                is_primary_key=False,
                is_nullable=False,
                description="Vendor company name"
            ),
            ColumnInfo(
                name="contact_email",
                data_type="varchar",
                is_primary_key=False,
                is_nullable=False,
                description="Primary contact email"
            ),
            ColumnInfo(
                name="contact_phone",
                data_type="varchar",
                is_primary_key=False,
                is_nullable=True,
                description="Primary contact phone"
            ),
            ColumnInfo(
                name="address",
                data_type="text",
                is_primary_key=False,
                is_nullable=True,
                description="Vendor address"
            ),
            ColumnInfo(
                name="tax_id",
                data_type="varchar",
                is_primary_key=False,
                is_nullable=True,
                description="Tax identification number"
            ),
            ColumnInfo(
                name="is_active",
                data_type="boolean",
                is_primary_key=False,
                is_nullable=False,
                description="Whether vendor is active"
            )
        ],
        primary_keys=["vendor_id"],
        foreign_keys=[],
        indexes=[
            IndexInfo(
                name="idx_vendors_name",
                columns=["vendor_name"],
                is_unique=False,
                is_primary=False
            ),
            IndexInfo(
                name="idx_vendors_email",
                columns=["contact_email"],
                is_unique=True,
                is_primary=False
            )
        ],
        row_count=500,
        size_bytes=1024000,
        business_domain="procurement"
    )
    
    # Purchase Orders table
    purchase_orders_table = TableInfo(
        name="purchase_orders",
        schema="dbo",
        columns=[
            ColumnInfo(
                name="po_id",
                data_type="int",
                is_primary_key=True,
                is_nullable=False,
                description="Unique purchase order identifier"
            ),
            ColumnInfo(
                name="po_number",
                data_type="varchar",
                is_primary_key=False,
                is_nullable=False,
                description="Purchase order number"
            ),
            ColumnInfo(
                name="vendor_id",
                data_type="int",
                is_primary_key=False,
                is_nullable=False,
                description="Vendor who will fulfill the order"
            ),
            ColumnInfo(
                name="requester_id",
                data_type="int",
                is_primary_key=False,
                is_nullable=False,
                description="Employee who requested the order"
            ),
            ColumnInfo(
                name="order_date",
                data_type="datetime",
                is_primary_key=False,
                is_nullable=False,
                description="Date when order was placed"
            ),
            ColumnInfo(
                name="expected_delivery",
                data_type="datetime",
                is_primary_key=False,
                is_nullable=True,
                description="Expected delivery date"
            ),
            ColumnInfo(
                name="total_amount",
                data_type="decimal",
                is_primary_key=False,
                is_nullable=False,
                description="Total order amount"
            ),
            ColumnInfo(
                name="status",
                data_type="varchar",
                is_primary_key=False,
                is_nullable=False,
                description="Order status (pending, approved, shipped, delivered)"
            )
        ],
        primary_keys=["po_id"],
        foreign_keys=[
            ForeignKeyInfo(
                constraint_name="fk_po_vendor",
                column_name="vendor_id",
                referenced_table="vendors",
                referenced_column="vendor_id",
                on_delete="RESTRICT",
                on_update="CASCADE"
            ),
            ForeignKeyInfo(
                constraint_name="fk_po_requester",
                column_name="requester_id",
                referenced_table="employees",
                referenced_column="employee_id",
                on_delete="RESTRICT",
                on_update="CASCADE"
            )
        ],
        indexes=[
            IndexInfo(
                name="idx_po_number",
                columns=["po_number"],
                is_unique=True,
                is_primary=False
            ),
            IndexInfo(
                name="idx_po_vendor",
                columns=["vendor_id"],
                is_unique=False,
                is_primary=False
            ),
            IndexInfo(
                name="idx_po_status",
                columns=["status"],
                is_unique=False,
                is_primary=False
            )
        ],
        row_count=2000,
        size_bytes=5120000,
        business_domain="procurement"
    )
    
    # Employees table
    employees_table = TableInfo(
        name="employees",
        schema="dbo",
        columns=[
            ColumnInfo(
                name="employee_id",
                data_type="int",
                is_primary_key=True,
                is_nullable=False,
                description="Unique employee identifier"
            ),
            ColumnInfo(
                name="first_name",
                data_type="varchar",
                is_primary_key=False,
                is_nullable=False,
                description="Employee first name"
            ),
            ColumnInfo(
                name="last_name",
                data_type="varchar",
                is_primary_key=False,
                is_nullable=False,
                description="Employee last name"
            ),
            ColumnInfo(
                name="email",
                data_type="varchar",
                is_primary_key=False,
                is_nullable=False,
                description="Employee email address"
            ),
            ColumnInfo(
                name="department_id",
                data_type="int",
                is_primary_key=False,
                is_nullable=False,
                description="Department where employee works"
            ),
            ColumnInfo(
                name="hire_date",
                data_type="date",
                is_primary_key=False,
                is_nullable=False,
                description="Date when employee was hired"
            ),
            ColumnInfo(
                name="salary",
                data_type="decimal",
                is_primary_key=False,
                is_nullable=True,
                description="Employee salary"
            )
        ],
        primary_keys=["employee_id"],
        foreign_keys=[
            ForeignKeyInfo(
                constraint_name="fk_employees_department",
                column_name="department_id",
                referenced_table="departments",
                referenced_column="department_id",
                on_delete="RESTRICT",
                on_update="CASCADE"
            )
        ],
        indexes=[
            IndexInfo(
                name="idx_employees_email",
                columns=["email"],
                is_unique=True,
                is_primary=False
            ),
            IndexInfo(
                name="idx_employees_department",
                columns=["department_id"],
                is_unique=False,
                is_primary=False
            )
        ],
        row_count=1000,
        size_bytes=1024000,
        business_domain="hr"
    )
    
    # Departments table
    departments_table = TableInfo(
        name="departments",
        schema="dbo",
        columns=[
            ColumnInfo(
                name="department_id",
                data_type="int",
                is_primary_key=True,
                is_nullable=False,
                description="Unique department identifier"
            ),
            ColumnInfo(
                name="department_name",
                data_type="varchar",
                is_primary_key=False,
                is_nullable=False,
                description="Department name"
            ),
            ColumnInfo(
                name="budget",
                data_type="decimal",
                is_primary_key=False,
                is_nullable=True,
                description="Department budget"
            ),
            ColumnInfo(
                name="manager_id",
                data_type="int",
                is_primary_key=False,
                is_nullable=True,
                description="Department manager"
            )
        ],
        primary_keys=["department_id"],
        foreign_keys=[
            ForeignKeyInfo(
                constraint_name="fk_departments_manager",
                column_name="manager_id",
                referenced_table="employees",
                referenced_column="employee_id",
                on_delete="SET NULL",
                on_update="CASCADE"
            )
        ],
        indexes=[
            IndexInfo(
                name="idx_departments_name",
                columns=["department_name"],
                is_unique=True,
                is_primary=False
            )
        ],
        row_count=50,
        size_bytes=51200,
        business_domain="hr"
    )
    
    # Products table
    products_table = TableInfo(
        name="products",
        schema="dbo",
        columns=[
            ColumnInfo(
                name="product_id",
                data_type="int",
                is_primary_key=True,
                is_nullable=False,
                description="Unique product identifier"
            ),
            ColumnInfo(
                name="product_name",
                data_type="varchar",
                is_primary_key=False,
                is_nullable=False,
                description="Product name"
            ),
            ColumnInfo(
                name="sku",
                data_type="varchar",
                is_primary_key=False,
                is_nullable=False,
                description="Product SKU"
            ),
            ColumnInfo(
                name="category_id",
                data_type="int",
                is_primary_key=False,
                is_nullable=False,
                description="Product category"
            ),
            ColumnInfo(
                name="unit_price",
                data_type="decimal",
                is_primary_key=False,
                is_nullable=False,
                description="Unit price"
            ),
            ColumnInfo(
                name="description",
                data_type="text",
                is_primary_key=False,
                is_nullable=True,
                description="Product description"
            )
        ],
        primary_keys=["product_id"],
        foreign_keys=[
            ForeignKeyInfo(
                constraint_name="fk_products_category",
                column_name="category_id",
                referenced_table="categories",
                referenced_column="category_id",
                on_delete="RESTRICT",
                on_update="CASCADE"
            )
        ],
        indexes=[
            IndexInfo(
                name="idx_products_sku",
                columns=["sku"],
                is_unique=True,
                is_primary=False
            ),
            IndexInfo(
                name="idx_products_category",
                columns=["category_id"],
                is_unique=False,
                is_primary=False
            )
        ],
        row_count=5000,
        size_bytes=5120000,
        business_domain="ecommerce"
    )
    
    # Categories table
    categories_table = TableInfo(
        name="categories",
        schema="dbo",
        columns=[
            ColumnInfo(
                name="category_id",
                data_type="int",
                is_primary_key=True,
                is_nullable=False,
                description="Unique category identifier"
            ),
            ColumnInfo(
                name="category_name",
                data_type="varchar",
                is_primary_key=False,
                is_nullable=False,
                description="Category name"
            ),
            ColumnInfo(
                name="parent_category_id",
                data_type="int",
                is_primary_key=False,
                is_nullable=True,
                description="Parent category for hierarchical structure"
            )
        ],
        primary_keys=["category_id"],
        foreign_keys=[
            ForeignKeyInfo(
                constraint_name="fk_categories_parent",
                column_name="parent_category_id",
                referenced_table="categories",
                referenced_column="category_id",
                on_delete="SET NULL",
                on_update="CASCADE"
            )
        ],
        indexes=[
            IndexInfo(
                name="idx_categories_name",
                columns=["category_name"],
                is_unique=True,
                is_primary=False
            )
        ],
        row_count=100,
        size_bytes=102400,
        business_domain="ecommerce"
    )
    
    # Purchase Order Items table
    po_items_table = TableInfo(
        name="purchase_order_items",
        schema="dbo",
        columns=[
            ColumnInfo(
                name="item_id",
                data_type="int",
                is_primary_key=True,
                is_nullable=False,
                description="Unique item identifier"
            ),
            ColumnInfo(
                name="po_id",
                data_type="int",
                is_primary_key=False,
                is_nullable=False,
                description="Purchase order this item belongs to"
            ),
            ColumnInfo(
                name="product_id",
                data_type="int",
                is_primary_key=False,
                is_nullable=False,
                description="Product being ordered"
            ),
            ColumnInfo(
                name="quantity",
                data_type="int",
                is_primary_key=False,
                is_nullable=False,
                description="Quantity ordered"
            ),
            ColumnInfo(
                name="unit_price",
                data_type="decimal",
                is_primary_key=False,
                is_nullable=False,
                description="Unit price at time of order"
            ),
            ColumnInfo(
                name="total_price",
                data_type="decimal",
                is_primary_key=False,
                is_nullable=False,
                description="Total price for this line item"
            )
        ],
        primary_keys=["item_id"],
        foreign_keys=[
            ForeignKeyInfo(
                constraint_name="fk_po_items_po",
                column_name="po_id",
                referenced_table="purchase_orders",
                referenced_column="po_id",
                on_delete="CASCADE",
                on_update="CASCADE"
            ),
            ForeignKeyInfo(
                constraint_name="fk_po_items_product",
                column_name="product_id",
                referenced_table="products",
                referenced_column="product_id",
                on_delete="RESTRICT",
                on_update="CASCADE"
            )
        ],
        indexes=[
            IndexInfo(
                name="idx_po_items_po",
                columns=["po_id"],
                is_unique=False,
                is_primary=False
            ),
            IndexInfo(
                name="idx_po_items_product",
                columns=["product_id"],
                is_unique=False,
                is_primary=False
            )
        ],
        row_count=8000,
        size_bytes=8192000,
        business_domain="procurement"
    )
    
    return DatabaseSchema(
        database_name="puma_procurement",
        tables=[
            vendors_table,
            purchase_orders_table,
            employees_table,
            departments_table,
            products_table,
            categories_table,
            po_items_table
        ],
        views=[],
        functions=[],
        procedures=[],
        total_size_bytes=52428800  # 50MB
    )


class MockDatabaseAdapter:
    """Mock database adapter for demonstration."""
    
    def __init__(self, schema: DatabaseSchema):
        self.schema = schema
        self.database_type = DatabaseType.SQLSERVER  # Set default type
        self.config = type('Config', (), {'database': schema.database_name})()
    
    async def get_schema(self, force_refresh: bool = False) -> DatabaseSchema:
        """Return the mock schema."""
        return self.schema


async def demonstrate_business_domain_detection(introspector: SchemaIntrospector, 
                                              schema: DatabaseSchema):
    """Demonstrate business domain detection capabilities."""
    print("\n" + "="*80)
    print("🔍 BUSINESS DOMAIN DETECTION")
    print("="*80)
    
    domains = await introspector._analyze_business_domains(schema.tables)
    
    print(f"\nDetected Business Domains:")
    for domain, tables in domains.items():
        print(f"  📊 {domain.value.upper()}: {', '.join(tables)}")
    
    print(f"\nTotal domains detected: {len(domains)}")
    
    # Show domain patterns
    print(f"\nAvailable domain patterns:")
    for pattern in introspector._domain_patterns:
        print(f"  🎯 {pattern.domain.value}: {len(pattern.keywords)} keywords, "
              f"{len(pattern.table_patterns)} table patterns")


async def demonstrate_relationship_analysis(introspector: SchemaIntrospector, 
                                          schema: DatabaseSchema):
    """Demonstrate relationship analysis capabilities."""
    print("\n" + "="*80)
    print("🔗 RELATIONSHIP ANALYSIS")
    print("="*80)
    
    relationships = await introspector._analyze_relationships(schema.tables)
    
    print(f"\nDetected Relationships ({len(relationships)} total):")
    for i, rel in enumerate(relationships, 1):
        print(f"  {i}. {rel.source_table} → {rel.target_table}")
        print(f"     Type: {rel.relationship_type.value}")
        print(f"     Confidence: {rel.confidence:.2f}")
        print(f"     Description: {rel.description}")
        print()
    
    # Show relationship types distribution
    type_counts = {}
    for rel in relationships:
        rel_type = rel.relationship_type.value
        type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
    
    print("Relationship Types Distribution:")
    for rel_type, count in type_counts.items():
        print(f"  📈 {rel_type}: {count}")


async def demonstrate_table_clustering(introspector: SchemaIntrospector, 
                                     schema: DatabaseSchema):
    """Demonstrate table clustering capabilities."""
    print("\n" + "="*80)
    print("📊 TABLE CLUSTERING")
    print("="*80)
    
    relationships = await introspector._analyze_relationships(schema.tables)
    clusters = await introspector._analyze_table_clusters(schema.tables, relationships)
    
    print(f"\nTable Clusters ({len(clusters)} clusters):")
    for cluster_name, tables in clusters.items():
        print(f"  🏷️  {cluster_name}: {', '.join(tables)}")
        print(f"     Size: {len(tables)} tables")
        print()
    
    # Show cluster analysis
    cluster_sizes = [len(tables) for tables in clusters.values()]
    if cluster_sizes:
        print(f"Cluster Statistics:")
        print(f"  📊 Average cluster size: {sum(cluster_sizes) / len(cluster_sizes):.1f}")
        print(f"  📊 Largest cluster: {max(cluster_sizes)} tables")
        print(f"  📊 Smallest cluster: {min(cluster_sizes)} tables")


async def demonstrate_data_quality_assessment(introspector: SchemaIntrospector, 
                                             schema: DatabaseSchema):
    """Demonstrate data quality assessment capabilities."""
    print("\n" + "="*80)
    print("✅ DATA QUALITY ASSESSMENT")
    print("="*80)
    
    quality_score = await introspector._calculate_data_quality_score(schema.tables)
    
    print(f"\nOverall Data Quality Score: {quality_score:.2f}/1.0")
    
    # Quality interpretation
    if quality_score >= 0.8:
        quality_level = "🟢 Excellent"
    elif quality_score >= 0.6:
        quality_level = "🟡 Good"
    elif quality_score >= 0.4:
        quality_level = "🟠 Fair"
    else:
        quality_level = "🔴 Poor"
    
    print(f"Quality Level: {quality_level}")
    
    # Show recommendations for each table
    print(f"\nTable-specific Recommendations:")
    for table in schema.tables:
        recommendations = await introspector.get_table_recommendations(table)
        if recommendations:
            print(f"  📋 {table.name}:")
            for rec in recommendations:
                print(f"    • {rec}")
        else:
            print(f"  ✅ {table.name}: No recommendations (well-structured)")


async def demonstrate_complexity_analysis(introspector: SchemaIntrospector, 
                                        schema: DatabaseSchema):
    """Demonstrate schema complexity analysis."""
    print("\n" + "="*80)
    print("🧮 SCHEMA COMPLEXITY ANALYSIS")
    print("="*80)
    
    relationships = await introspector._analyze_relationships(schema.tables)
    complexity_score = await introspector._calculate_complexity_score(schema.tables, relationships)
    
    print(f"\nSchema Complexity Score: {complexity_score:.2f}/1.0")
    
    # Complexity interpretation
    if complexity_score >= 0.7:
        complexity_level = "🔴 High"
    elif complexity_score >= 0.4:
        complexity_level = "🟡 Medium"
    else:
        complexity_level = "🟢 Low"
    
    print(f"Complexity Level: {complexity_level}")
    
    # Show complexity breakdown
    total_tables = len(schema.tables)
    total_columns = sum(len(table.columns) for table in schema.tables)
    total_relationships = len(relationships)
    total_fks = sum(len(table.foreign_keys) for table in schema.tables)
    
    print(f"\nComplexity Breakdown:")
    print(f"  📊 Tables: {total_tables}")
    print(f"  📊 Columns: {total_columns}")
    print(f"  📊 Relationships: {total_relationships}")
    print(f"  📊 Foreign Keys: {total_fks}")
    print(f"  📊 Average columns per table: {total_columns / total_tables:.1f}")
    print(f"  📊 Average relationships per table: {total_relationships / total_tables:.1f}")


async def demonstrate_schema_documentation(introspector: SchemaIntrospector, 
                                         mock_adapter):
    """Demonstrate schema documentation generation."""
    print("\n" + "="*80)
    print("📚 SCHEMA DOCUMENTATION GENERATION")
    print("="*80)
    
    analysis = await introspector.analyze_schema(mock_adapter)
    documentation = await introspector.generate_schema_documentation(analysis)
    
    print(f"\nGenerated Documentation Preview:")
    print("-" * 40)
    
    # Show first 20 lines of documentation
    lines = documentation.split('\n')
    for i, line in enumerate(lines[:20]):
        print(f"{i+1:2d}: {line}")
    
    if len(lines) > 20:
        print(f"... ({len(lines) - 20} more lines)")
    
    print(f"\nFull documentation length: {len(documentation)} characters")


async def demonstrate_caching_and_performance(introspector: SchemaIntrospector, 
                                             mock_adapter):
    """Demonstrate caching and performance features."""
    print("\n" + "="*80)
    print("⚡ CACHING AND PERFORMANCE")
    print("="*80)
    
    import time
    
    # First analysis (cold cache)
    start_time = time.time()
    analysis1 = await introspector.analyze_schema(mock_adapter)
    cold_time = time.time() - start_time
    
    # Second analysis (warm cache)
    start_time = time.time()
    analysis2 = await introspector.analyze_schema(mock_adapter)
    warm_time = time.time() - start_time
    
    # Force refresh
    start_time = time.time()
    analysis3 = await introspector.analyze_schema(mock_adapter, force_refresh=True)
    refresh_time = time.time() - start_time
    
    print(f"\nPerformance Metrics:")
    print(f"  🕐 Cold analysis: {cold_time:.3f} seconds")
    print(f"  🕐 Warm analysis: {warm_time:.3f} seconds")
    print(f"  🕐 Force refresh: {refresh_time:.3f} seconds")
    
    if warm_time < cold_time and warm_time > 0:
        speedup = cold_time / warm_time
        print(f"  ⚡ Cache speedup: {speedup:.1f}x faster")
    
    # Verify caching
    print(f"\nCache Verification:")
    print(f"  🔄 Same analysis object: {analysis1 is analysis2}")
    print(f"  🔄 Different after refresh: {analysis1 is not analysis3}")
    print(f"  📊 Cache size: {len(introspector._analysis_cache)} entries")


async def main():
    """Main demonstration function."""
    print("🚀 SCHEMA INTROSPECTION ENGINE DEMONSTRATION")
    print("=" * 80)
    print("This demo showcases the comprehensive schema analysis capabilities")
    print("of the Global RAG Platform's Schema Introspection Engine.")
    print("=" * 80)
    
    # Create sample schema
    print("\n📋 Creating sample Puma procurement database schema...")
    schema = create_sample_procurement_schema()
    print(f"✅ Created schema with {len(schema.tables)} tables")
    
    # Create mock adapter
    mock_adapter = MockDatabaseAdapter(schema)
    
    # Get schema introspector
    introspector = get_schema_introspector()
    
    # Run demonstrations
    await demonstrate_business_domain_detection(introspector, schema)
    await demonstrate_relationship_analysis(introspector, schema)
    await demonstrate_table_clustering(introspector, schema)
    await demonstrate_data_quality_assessment(introspector, schema)
    await demonstrate_complexity_analysis(introspector, schema)
    await demonstrate_schema_documentation(introspector, mock_adapter)
    await demonstrate_caching_and_performance(introspector, mock_adapter)
    
    # Summary
    print("\n" + "="*80)
    print("📊 DEMONSTRATION SUMMARY")
    print("="*80)
    
    analysis = await introspector.analyze_schema(mock_adapter)
    
    print(f"\nSchema Analysis Results:")
    print(f"  🗄️  Database: {analysis.database_name}")
    print(f"  🗄️  Type: {analysis.database_type.value}")
    print(f"  📊 Tables: {analysis.total_tables}")
    print(f"  📊 Columns: {analysis.total_columns}")
    print(f"  🔗 Relationships: {analysis.total_relationships}")
    print(f"  🎯 Business Domains: {len(analysis.business_domains)}")
    print(f"  📈 Data Quality: {analysis.data_quality_score:.2f}/1.0")
    print(f"  🧮 Complexity: {analysis.complexity_score:.2f}/1.0")
    
    print(f"\n✅ Schema Introspection Engine demonstration completed successfully!")
    print(f"🔧 The engine is ready for integration with the Global RAG Platform.")


if __name__ == "__main__":
    asyncio.run(main())
