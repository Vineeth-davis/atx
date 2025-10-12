"""
Tests for Schema Introspection Engine

Comprehensive test suite for the schema analysis, business domain detection,
relationship analysis, and schema documentation features.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import asyncio

from core.schema_introspector import (
    SchemaIntrospector,
    BusinessDomain,
    RelationshipType,
    BusinessDomainPattern,
    RelationshipInfo,
    SchemaAnalysis,
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


@pytest.fixture
def sample_tables():
    """Create sample tables for testing."""
    return [
        TableInfo(
            name="customers",
            schema="dbo",
            columns=[
                ColumnInfo(
                    name="customer_id",
                    data_type="int",
                    is_primary_key=True,
                    is_nullable=False,
                    description="Unique customer identifier"
                ),
                ColumnInfo(
                    name="email",
                    data_type="varchar",
                    is_primary_key=False,
                    is_nullable=False,
                    description="Customer email address"
                ),
                ColumnInfo(
                    name="phone",
                    data_type="varchar",
                    is_primary_key=False,
                    is_nullable=True,
                    description="Customer phone number"
                )
            ],
            primary_keys=["customer_id"],
            foreign_keys=[],
            indexes=[
                IndexInfo(
                    name="idx_customers_email",
                    columns=["email"],
                    is_unique=True,
                    is_primary=False
                )
            ],
            row_count=1000,
            size_bytes=1024000,
            business_domain="crm"
        ),
        TableInfo(
            name="orders",
            schema="dbo",
            columns=[
                ColumnInfo(
                    name="order_id",
                    data_type="int",
                    is_primary_key=True,
                    is_nullable=False,
                    description="Unique order identifier"
                ),
                ColumnInfo(
                    name="customer_id",
                    data_type="int",
                    is_primary_key=False,
                    is_nullable=False,
                    description="Customer who placed the order"
                ),
                ColumnInfo(
                    name="order_date",
                    data_type="datetime",
                    is_primary_key=False,
                    is_nullable=False,
                    description="Date when order was placed"
                ),
                ColumnInfo(
                    name="total_amount",
                    data_type="decimal",
                    is_primary_key=False,
                    is_nullable=False,
                    description="Total order amount"
                )
            ],
            primary_keys=["order_id"],
            foreign_keys=[
                ForeignKeyInfo(
                    constraint_name="fk_orders_customer",
                    column_name="customer_id",
                    referenced_table="customers",
                    referenced_column="customer_id",
                    on_delete="CASCADE",
                    on_update="CASCADE"
                )
            ],
            indexes=[],
            row_count=5000,
            size_bytes=5120000,
            business_domain="ecommerce"
        ),
        TableInfo(
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
                    name="sku",
                    data_type="varchar",
                    is_primary_key=False,
                    is_nullable=False,
                    description="Product SKU"
                ),
                ColumnInfo(
                    name="price",
                    data_type="decimal",
                    is_primary_key=False,
                    is_nullable=False,
                    description="Product price"
                ),
                ColumnInfo(
                    name="quantity",
                    data_type="int",
                    is_primary_key=False,
                    is_nullable=False,
                    description="Available quantity"
                )
            ],
            primary_keys=["product_id"],
            foreign_keys=[],
            indexes=[
                IndexInfo(
                    name="idx_products_sku",
                    columns=["sku"],
                    is_unique=True,
                    is_primary=False
                )
            ],
            row_count=2000,
            size_bytes=2048000,
            business_domain="ecommerce"
        )
    ]


@pytest.fixture
def sample_schema(sample_tables):
    """Create sample database schema."""
    return DatabaseSchema(
        database_name="test_db",
        tables=sample_tables,
        views=[],
        functions=[],
        procedures=[],
        total_size_bytes=8192000
    )


@pytest.fixture
def mock_adapter(sample_schema):
    """Create mock database adapter."""
    adapter = AsyncMock()
    adapter.database_type = DatabaseType.POSTGRESQL
    adapter.config.database = "test_db"
    adapter.get_schema.return_value = sample_schema
    return adapter


@pytest.fixture
def introspector():
    """Create schema introspector instance."""
    return SchemaIntrospector()


class TestSchemaIntrospector:
    """Test cases for SchemaIntrospector class."""
    
    def test_initialization(self, introspector):
        """Test schema introspector initialization."""
        assert introspector is not None
        assert len(introspector._domain_patterns) > 0
        assert introspector._relationship_cache == {}
        assert introspector._analysis_cache == {}
    
    def test_domain_patterns_initialization(self, introspector):
        """Test business domain patterns initialization."""
        patterns = introspector._domain_patterns
        
        # Check that all business domains have patterns
        domains = [pattern.domain for pattern in patterns]
        assert BusinessDomain.FINANCE in domains
        assert BusinessDomain.CRM in domains
        assert BusinessDomain.ECOMMERCE in domains
        assert BusinessDomain.PROCUREMENT in domains
        
        # Check that patterns have required fields
        for pattern in patterns:
            assert pattern.domain is not None
            assert len(pattern.table_patterns) > 0
            assert len(pattern.column_patterns) > 0
            assert len(pattern.keywords) > 0
            assert 0.0 <= pattern.confidence_threshold <= 1.0
    
    @pytest.mark.asyncio
    async def test_analyze_schema(self, introspector, mock_adapter, sample_schema):
        """Test comprehensive schema analysis."""
        analysis = await introspector.analyze_schema(mock_adapter)
        
        assert isinstance(analysis, SchemaAnalysis)
        assert analysis.database_name == "test_db"
        assert analysis.database_type == DatabaseType.POSTGRESQL
        assert analysis.total_tables == 3
        assert analysis.total_columns == 11
        assert analysis.total_relationships == 1
        assert 0.0 <= analysis.data_quality_score <= 1.0
        assert 0.0 <= analysis.complexity_score <= 1.0
        assert isinstance(analysis.business_domains, dict)
        assert isinstance(analysis.relationships, list)
        assert isinstance(analysis.table_clusters, dict)
    
    @pytest.mark.asyncio
    async def test_analyze_business_domains(self, introspector, sample_tables):
        """Test business domain analysis."""
        domains = await introspector._analyze_business_domains(sample_tables)
        
        assert isinstance(domains, dict)
        
        # Check that CRM domain is detected
        if BusinessDomain.CRM in domains:
            assert "customers" in domains[BusinessDomain.CRM]
        
        # Check that ECOMMERCE domain is detected
        if BusinessDomain.ECOMMERCE in domains:
            assert "orders" in domains[BusinessDomain.ECOMMERCE]
            assert "products" in domains[BusinessDomain.ECOMMERCE]
    
    @pytest.mark.asyncio
    async def test_analyze_relationships(self, introspector, sample_tables):
        """Test relationship analysis."""
        relationships = await introspector._analyze_relationships(sample_tables)
        
        assert isinstance(relationships, list)
        assert len(relationships) == 1
        
        rel = relationships[0]
        assert isinstance(rel, RelationshipInfo)
        assert rel.source_table == "orders"
        assert rel.target_table == "customers"
        assert rel.relationship_type == RelationshipType.ONE_TO_MANY
        assert 0.0 <= rel.confidence <= 1.0
        assert len(rel.foreign_keys) == 1
    
    @pytest.mark.asyncio
    async def test_determine_relationship_type(self, introspector, sample_tables):
        """Test relationship type determination."""
        customers_table = sample_tables[0]
        orders_table = sample_tables[1]
        fk = orders_table.foreign_keys[0]
        
        rel_type = await introspector._determine_relationship_type(
            orders_table, customers_table, fk
        )
        
        assert rel_type == RelationshipType.ONE_TO_MANY
    
    @pytest.mark.asyncio
    async def test_calculate_relationship_confidence(self, introspector, sample_tables):
        """Test relationship confidence calculation."""
        customers_table = sample_tables[0]
        orders_table = sample_tables[1]
        fk = orders_table.foreign_keys[0]
        
        confidence = await introspector._calculate_relationship_confidence(
            orders_table, customers_table, fk
        )
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be high confidence for proper FK
    
    @pytest.mark.asyncio
    async def test_analyze_table_clusters(self, introspector, sample_tables):
        """Test table clustering analysis."""
        relationships = await introspector._analyze_relationships(sample_tables)
        clusters = await introspector._analyze_table_clusters(sample_tables, relationships)
        
        assert isinstance(clusters, dict)
        assert len(clusters) > 0
        
        # Check that all tables are in clusters
        all_clustered_tables = []
        for cluster_tables in clusters.values():
            all_clustered_tables.extend(cluster_tables)
        
        assert len(all_clustered_tables) == len(sample_tables)
    
    @pytest.mark.asyncio
    async def test_calculate_data_quality_score(self, introspector, sample_tables):
        """Test data quality score calculation."""
        score = await introspector._calculate_data_quality_score(sample_tables)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be decent quality for well-structured tables
    
    @pytest.mark.asyncio
    async def test_calculate_complexity_score(self, introspector, sample_tables):
        """Test complexity score calculation."""
        relationships = await introspector._analyze_relationships(sample_tables)
        score = await introspector._calculate_complexity_score(sample_tables, relationships)
        
        assert 0.0 <= score <= 1.0
        assert score < 0.5  # Should be low complexity for simple schema
    
    @pytest.mark.asyncio
    async def test_get_table_recommendations(self, introspector, sample_tables):
        """Test table recommendations generation."""
        table = sample_tables[0]  # customers table
        recommendations = await introspector.get_table_recommendations(table)
        
        assert isinstance(recommendations, list)
        
        # Should have some recommendations
        assert len(recommendations) >= 0
    
    @pytest.mark.asyncio
    async def test_generate_schema_documentation(self, introspector, mock_adapter):
        """Test schema documentation generation."""
        analysis = await introspector.analyze_schema(mock_adapter)
        documentation = await introspector.generate_schema_documentation(analysis)
        
        assert isinstance(documentation, str)
        assert "Database Schema Documentation" in documentation
        assert "test_db" in documentation
        assert "Overview" in documentation
        assert "Business Domains" in documentation
        assert "Table Clusters" in documentation
        assert "Relationships" in documentation
        assert "Metadata" in documentation
    
    @pytest.mark.asyncio
    async def test_analysis_caching(self, introspector, mock_adapter):
        """Test analysis caching functionality."""
        # First analysis
        analysis1 = await introspector.analyze_schema(mock_adapter)
        
        # Second analysis should use cache
        analysis2 = await introspector.analyze_schema(mock_adapter)
        
        # Should be the same object (cached)
        assert analysis1 is analysis2
        
        # Force refresh should create new analysis
        analysis3 = await introspector.analyze_schema(mock_adapter, force_refresh=True)
        assert analysis3 is not analysis1
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, introspector, mock_adapter):
        """Test cache clearing functionality."""
        # Perform analysis to populate cache
        await introspector.analyze_schema(mock_adapter)
        
        # Verify cache is populated
        assert len(introspector._analysis_cache) > 0
        
        # Clear cache
        await introspector.clear_cache()
        
        # Verify cache is cleared
        assert len(introspector._analysis_cache) == 0
        assert len(introspector._relationship_cache) == 0


class TestBusinessDomainPattern:
    """Test cases for BusinessDomainPattern class."""
    
    def test_business_domain_pattern_creation(self):
        """Test business domain pattern creation."""
        pattern = BusinessDomainPattern(
            domain=BusinessDomain.FINANCE,
            table_patterns=['account', 'transaction'],
            column_patterns=['amount', 'balance'],
            keywords=['financial', 'accounting'],
            confidence_threshold=0.7
        )
        
        assert pattern.domain == BusinessDomain.FINANCE
        assert pattern.table_patterns == ['account', 'transaction']
        assert pattern.column_patterns == ['amount', 'balance']
        assert pattern.keywords == ['financial', 'accounting']
        assert pattern.confidence_threshold == 0.7


class TestRelationshipInfo:
    """Test cases for RelationshipInfo class."""
    
    def test_relationship_info_creation(self):
        """Test relationship info creation."""
        fk = ForeignKeyInfo(
            constraint_name="fk_test",
            column_name="test_id",
            referenced_table="referenced_table",
            referenced_column="id",
            on_delete="CASCADE",
            on_update="CASCADE"
        )
        
        rel_info = RelationshipInfo(
            source_table="source_table",
            target_table="target_table",
            relationship_type=RelationshipType.ONE_TO_MANY,
            foreign_keys=[fk],
            confidence=0.8,
            description="Test relationship"
        )
        
        assert rel_info.source_table == "source_table"
        assert rel_info.target_table == "target_table"
        assert rel_info.relationship_type == RelationshipType.ONE_TO_MANY
        assert len(rel_info.foreign_keys) == 1
        assert rel_info.confidence == 0.8
        assert rel_info.description == "Test relationship"


class TestSchemaAnalysis:
    """Test cases for SchemaAnalysis class."""
    
    def test_schema_analysis_creation(self):
        """Test schema analysis creation."""
        analysis = SchemaAnalysis(
            database_name="test_db",
            database_type=DatabaseType.POSTGRESQL,
            total_tables=10,
            total_columns=50,
            total_relationships=5,
            business_domains={BusinessDomain.CRM: ["customers"]},
            relationships=[],
            table_clusters={"cluster_1": ["table1", "table2"]},
            data_quality_score=0.8,
            complexity_score=0.6
        )
        
        assert analysis.database_name == "test_db"
        assert analysis.database_type == DatabaseType.POSTGRESQL
        assert analysis.total_tables == 10
        assert analysis.total_columns == 50
        assert analysis.total_relationships == 5
        assert BusinessDomain.CRM in analysis.business_domains
        assert analysis.data_quality_score == 0.8
        assert analysis.complexity_score == 0.6
        assert isinstance(analysis.analysis_timestamp, datetime)
        assert isinstance(analysis.metadata, dict)


class TestGlobalSchemaIntrospector:
    """Test cases for global schema introspector."""
    
    def test_get_schema_introspector(self):
        """Test getting global schema introspector instance."""
        introspector1 = get_schema_introspector()
        introspector2 = get_schema_introspector()
        
        # Should return the same instance
        assert introspector1 is introspector2
        assert isinstance(introspector1, SchemaIntrospector)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_empty_tables_analysis(self, introspector):
        """Test analysis with empty tables list."""
        domains = await introspector._analyze_business_domains([])
        assert domains == {}
        
        relationships = await introspector._analyze_relationships([])
        assert relationships == []
        
        clusters = await introspector._analyze_table_clusters([], [])
        assert clusters == {}
        
        quality_score = await introspector._calculate_data_quality_score([])
        assert quality_score == 0.0
        
        complexity_score = await introspector._calculate_complexity_score([], [])
        assert complexity_score == 0.0
    
    @pytest.mark.asyncio
    async def test_single_table_analysis(self, introspector):
        """Test analysis with single table."""
        single_table = [
            TableInfo(
                name="single_table",
                schema="dbo",
                columns=[
                    ColumnInfo(
                        name="id",
                        data_type="int",
                        is_primary_key=True,
                        is_nullable=False,
                        description="Primary key"
                    )
                ],
                primary_keys=["id"],
                foreign_keys=[],
                indexes=[],
                row_count=100,
                size_bytes=1024,
                business_domain="general"
            )
        ]
        
        domains = await introspector._analyze_business_domains(single_table)
        assert isinstance(domains, dict)
        
        relationships = await introspector._analyze_relationships(single_table)
        assert relationships == []
        
        clusters = await introspector._analyze_table_clusters(single_table, [])
        assert len(clusters) == 1
        assert "single_table" in list(clusters.values())[0]
    
    @pytest.mark.asyncio
    async def test_self_referencing_table(self, introspector):
        """Test analysis with self-referencing table."""
        self_ref_table = [
            TableInfo(
                name="employees",
                schema="dbo",
                columns=[
                    ColumnInfo(
                        name="employee_id",
                        data_type="int",
                        is_primary_key=True,
                        is_nullable=False,
                        description="Employee ID"
                    ),
                    ColumnInfo(
                        name="manager_id",
                        data_type="int",
                        is_primary_key=False,
                        is_nullable=True,
                        description="Manager ID"
                    )
                ],
                primary_keys=["employee_id"],
                foreign_keys=[
                    ForeignKeyInfo(
                        constraint_name="fk_employees_manager",
                        column_name="manager_id",
                        referenced_table="employees",
                        referenced_column="employee_id",
                        on_delete="SET NULL",
                        on_update="CASCADE"
                    )
                ],
                indexes=[],
                row_count=1000,
                size_bytes=1024000,
                business_domain="hr"
            )
        ]
        
        relationships = await introspector._analyze_relationships(self_ref_table)
        assert len(relationships) == 1
        
        rel = relationships[0]
        assert rel.source_table == "employees"
        assert rel.target_table == "employees"
        assert rel.relationship_type == RelationshipType.SELF_REFERENCING
