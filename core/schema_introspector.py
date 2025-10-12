"""
Schema Introspection Engine

A comprehensive schema discovery and mapping system that automatically analyzes
database schemas, detects relationships, business domains, and provides intelligent
schema understanding for the RAG platform.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from collections import defaultdict

from adapters.database_adapter import (
    DatabaseAdapter,
    DatabaseType,
    DatabaseSchema,
    TableInfo,
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo,
    ConnectionConfig
)

logger = logging.getLogger(__name__)


class BusinessDomain(Enum):
    """Business domain enumeration"""
    FINANCE = "finance"
    CRM = "crm"
    ECOMMERCE = "ecommerce"
    PROCUREMENT = "procurement"
    HR = "hr"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    EDUCATION = "education"
    REAL_ESTATE = "real_estate"
    LOGISTICS = "logistics"
    GENERAL = "general"


class RelationshipType(Enum):
    """Relationship type enumeration"""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"
    SELF_REFERENCING = "self_referencing"


@dataclass
class BusinessDomainPattern:
    """Pattern for business domain detection"""
    domain: BusinessDomain
    table_patterns: List[str]
    column_patterns: List[str]
    keywords: List[str]
    confidence_threshold: float = 0.7


@dataclass
class RelationshipInfo:
    """Information about table relationships"""
    source_table: str
    target_table: str
    relationship_type: RelationshipType
    foreign_keys: List[ForeignKeyInfo]
    confidence: float
    description: Optional[str] = None


@dataclass
class SchemaAnalysis:
    """Complete schema analysis result"""
    database_name: str
    database_type: DatabaseType
    total_tables: int
    total_columns: int
    total_relationships: int
    business_domains: Dict[BusinessDomain, List[str]]
    relationships: List[RelationshipInfo]
    table_clusters: Dict[str, List[str]]
    data_quality_score: float
    complexity_score: float
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SchemaIntrospector:
    """
    Advanced schema introspection engine.
    
    Features:
    - Complete schema discovery and mapping
    - Business domain detection
    - Relationship analysis
    - Data quality assessment
    - Schema complexity analysis
    - Table clustering and grouping
    - Performance optimization recommendations
    """
    
    def __init__(self):
        """Initialize schema introspector."""
        self._domain_patterns = self._initialize_domain_patterns()
        self._relationship_cache: Dict[str, List[RelationshipInfo]] = {}
        self._analysis_cache: Dict[str, SchemaAnalysis] = {}
        
    def _initialize_domain_patterns(self) -> List[BusinessDomainPattern]:
        """Initialize business domain detection patterns."""
        return [
            BusinessDomainPattern(
                domain=BusinessDomain.FINANCE,
                table_patterns=['account', 'transaction', 'payment', 'invoice', 'financial', 'ledger', 'budget'],
                column_patterns=['amount', 'balance', 'currency', 'price', 'cost', 'revenue', 'profit'],
                keywords=['financial', 'accounting', 'banking', 'payment', 'transaction', 'invoice']
            ),
            BusinessDomainPattern(
                domain=BusinessDomain.CRM,
                table_patterns=['customer', 'contact', 'lead', 'opportunity', 'client', 'prospect'],
                column_patterns=['email', 'phone', 'address', 'company', 'contact_name'],
                keywords=['customer', 'relationship', 'sales', 'marketing', 'lead']
            ),
            BusinessDomainPattern(
                domain=BusinessDomain.ECOMMERCE,
                table_patterns=['product', 'order', 'cart', 'inventory', 'shipping', 'category'],
                column_patterns=['sku', 'price', 'quantity', 'weight', 'dimensions'],
                keywords=['ecommerce', 'online', 'shopping', 'retail', 'product']
            ),
            BusinessDomainPattern(
                domain=BusinessDomain.PROCUREMENT,
                table_patterns=['purchase', 'vendor', 'supplier', 'procurement', 'requisition', 'po'],
                column_patterns=['vendor_id', 'po_number', 'requisition_id', 'approval_status'],
                keywords=['procurement', 'purchase', 'vendor', 'supplier', 'requisition']
            ),
            BusinessDomainPattern(
                domain=BusinessDomain.HR,
                table_patterns=['employee', 'hr', 'payroll', 'attendance', 'department', 'position'],
                column_patterns=['employee_id', 'salary', 'hire_date', 'department_id'],
                keywords=['human resources', 'employee', 'payroll', 'hr']
            ),
            BusinessDomainPattern(
                domain=BusinessDomain.HEALTHCARE,
                table_patterns=['patient', 'medical', 'health', 'diagnosis', 'treatment', 'appointment'],
                column_patterns=['patient_id', 'medical_record', 'diagnosis_code', 'treatment_date'],
                keywords=['healthcare', 'medical', 'patient', 'hospital', 'clinic']
            ),
            BusinessDomainPattern(
                domain=BusinessDomain.MANUFACTURING,
                table_patterns=['production', 'manufacturing', 'quality', 'assembly', 'workorder'],
                column_patterns=['production_id', 'assembly_line', 'quality_score', 'work_order'],
                keywords=['manufacturing', 'production', 'factory', 'assembly', 'quality']
            ),
            BusinessDomainPattern(
                domain=BusinessDomain.EDUCATION,
                table_patterns=['student', 'course', 'enrollment', 'grade', 'instructor', 'curriculum'],
                column_patterns=['student_id', 'course_code', 'grade', 'enrollment_date'],
                keywords=['education', 'school', 'university', 'student', 'course']
            ),
            BusinessDomainPattern(
                domain=BusinessDomain.REAL_ESTATE,
                table_patterns=['property', 'listing', 'agent', 'client', 'transaction'],
                column_patterns=['property_id', 'listing_price', 'square_feet', 'bedrooms'],
                keywords=['real estate', 'property', 'listing', 'agent', 'realtor']
            ),
            BusinessDomainPattern(
                domain=BusinessDomain.LOGISTICS,
                table_patterns=['shipment', 'delivery', 'warehouse', 'inventory', 'route'],
                column_patterns=['tracking_number', 'delivery_date', 'warehouse_id', 'route_id'],
                keywords=['logistics', 'shipping', 'delivery', 'warehouse', 'transport']
            )
        ]
    
    async def analyze_schema(self, adapter: DatabaseAdapter, 
                           force_refresh: bool = False) -> SchemaAnalysis:
        """
        Perform comprehensive schema analysis.
        
        Args:
            adapter: Database adapter
            force_refresh: Force refresh of cached analysis
            
        Returns:
            SchemaAnalysis: Complete schema analysis
        """
        cache_key = f"{adapter.database_type.value}_{adapter.config.database}"
        
        if not force_refresh and cache_key in self._analysis_cache:
            cached_analysis = self._analysis_cache[cache_key]
            cache_age = (datetime.utcnow() - cached_analysis.analysis_timestamp).total_seconds()
            if cache_age < 3600:  # 1 hour cache
                logger.info(f"Using cached schema analysis for {cache_key}")
                return cached_analysis
        
        logger.info(f"Starting schema analysis for {adapter.database_type.value} database")
        
        # Get database schema
        schema = await adapter.get_schema(force_refresh)
        
        # Analyze business domains
        business_domains = await self._analyze_business_domains(schema.tables)
        
        # Analyze relationships
        relationships = await self._analyze_relationships(schema.tables)
        
        # Analyze table clusters
        table_clusters = await self._analyze_table_clusters(schema.tables, relationships)
        
        # Calculate data quality score
        data_quality_score = await self._calculate_data_quality_score(schema.tables)
        
        # Calculate complexity score
        complexity_score = await self._calculate_complexity_score(schema.tables, relationships)
        
        analysis = SchemaAnalysis(
            database_name=schema.database_name,
            database_type=adapter.database_type,
            total_tables=len(schema.tables),
            total_columns=sum(len(table.columns) for table in schema.tables),
            total_relationships=len(relationships),
            business_domains=business_domains,
            relationships=relationships,
            table_clusters=table_clusters,
            data_quality_score=data_quality_score,
            complexity_score=complexity_score,
            metadata={
                'schema_version': schema.version,
                'total_size_bytes': schema.total_size_bytes,
                'functions_count': len(schema.functions),
                'procedures_count': len(schema.procedures),
                'views_count': len(schema.views)
            }
        )
        
        # Cache the analysis
        self._analysis_cache[cache_key] = analysis
        
        logger.info(f"Schema analysis completed for {adapter.database_type.value} database")
        return analysis
    
    async def _analyze_business_domains(self, tables: List[TableInfo]) -> Dict[BusinessDomain, List[str]]:
        """
        Analyze business domains from table names and columns.
        
        Args:
            tables: List of table information
            
        Returns:
            Dict: Business domains mapped to table names
        """
        domain_tables = defaultdict(list)
        
        for table in tables:
            table_domain_scores = {}
            
            for pattern in self._domain_patterns:
                score = 0.0
                
                # Check table name patterns
                table_name_lower = table.name.lower()
                for table_pattern in pattern.table_patterns:
                    if table_pattern in table_name_lower:
                        score += 0.3
                
                # Check column patterns
                column_names = [col.name.lower() for col in table.columns]
                for column_pattern in pattern.column_patterns:
                    if any(column_pattern in col_name for col_name in column_names):
                        score += 0.2
                
                # Check business domain from table metadata
                if table.business_domain and table.business_domain in pattern.keywords:
                    score += 0.4
                
                # Check column descriptions
                for col in table.columns:
                    if col.description:
                        desc_lower = col.description.lower()
                        for keyword in pattern.keywords:
                            if keyword in desc_lower:
                                score += 0.1
                
                table_domain_scores[pattern.domain] = score
            
            # Find the best matching domain
            if table_domain_scores:
                best_domain = max(table_domain_scores.items(), key=lambda x: x[1])
                if best_domain[1] >= 0.3:  # Minimum confidence threshold
                    domain_tables[best_domain[0]].append(table.name)
        
        return dict(domain_tables)
    
    async def _analyze_relationships(self, tables: List[TableInfo]) -> List[RelationshipInfo]:
        """
        Analyze relationships between tables.
        
        Args:
            tables: List of table information
            
        Returns:
            List: Relationship information
        """
        relationships = []
        table_dict = {table.name: table for table in tables}
        
        for table in tables:
            for fk in table.foreign_keys:
                if fk.referenced_table in table_dict:
                    target_table = table_dict[fk.referenced_table]
                    
                    # Determine relationship type
                    relationship_type = await self._determine_relationship_type(
                        table, target_table, fk
                    )
                    
                    # Calculate confidence
                    confidence = await self._calculate_relationship_confidence(
                        table, target_table, fk
                    )
                    
                    relationship = RelationshipInfo(
                        source_table=table.name,
                        target_table=fk.referenced_table,
                        relationship_type=relationship_type,
                        foreign_keys=[fk],
                        confidence=confidence,
                        description=f"{table.name} -> {fk.referenced_table}"
                    )
                    
                    relationships.append(relationship)
        
        return relationships
    
    async def _determine_relationship_type(self, source_table: TableInfo, 
                                         target_table: TableInfo, 
                                         fk: ForeignKeyInfo) -> RelationshipType:
        """
        Determine the type of relationship between tables.
        
        Args:
            source_table: Source table information
            target_table: Target table information
            fk: Foreign key information
            
        Returns:
            RelationshipType: Type of relationship
        """
        # Check for self-referencing
        if source_table.name == target_table.name:
            return RelationshipType.SELF_REFERENCING
        
        # Check for one-to-one (both tables have unique constraints on the FK column)
        source_fk_column = next((col for col in source_table.columns 
                               if col.name == fk.column_name), None)
        target_pk_column = next((col for col in target_table.columns 
                               if col.name == fk.referenced_column), None)
        
        if source_fk_column and target_pk_column:
            if source_fk_column.is_unique and target_pk_column.is_primary_key:
                return RelationshipType.ONE_TO_ONE
        
        # Default to one-to-many
        return RelationshipType.ONE_TO_MANY
    
    async def _calculate_relationship_confidence(self, source_table: TableInfo,
                                              target_table: TableInfo,
                                              fk: ForeignKeyInfo) -> float:
        """
        Calculate confidence score for a relationship.
        
        Args:
            source_table: Source table information
            target_table: Target table information
            fk: Foreign key information
            
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence
        
        # Check if foreign key column exists
        source_fk_column = next((col for col in source_table.columns 
                               if col.name == fk.column_name), None)
        if source_fk_column:
            confidence += 0.2
        
        # Check if referenced column exists
        target_pk_column = next((col for col in target_table.columns 
                               if col.name == fk.referenced_column), None)
        if target_pk_column:
            confidence += 0.2
        
        # Check naming conventions
        if fk.column_name.lower().endswith('_id'):
            confidence += 0.1
        
        # Check if referenced column is primary key
        if target_pk_column and target_pk_column.is_primary_key:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def _analyze_table_clusters(self, tables: List[TableInfo], 
                                    relationships: List[RelationshipInfo]) -> Dict[str, List[str]]:
        """
        Analyze table clusters based on relationships and business domains.
        
        Args:
            tables: List of table information
            relationships: List of relationship information
            
        Returns:
            Dict: Table clusters
        """
        clusters = defaultdict(list)
        visited = set()
        
        # Create adjacency list for relationships
        adjacency = defaultdict(list)
        for rel in relationships:
            adjacency[rel.source_table].append(rel.target_table)
            adjacency[rel.target_table].append(rel.source_table)
        
        # Find connected components
        for table in tables:
            if table.name not in visited:
                cluster_tables = []
                stack = [table.name]
                
                while stack:
                    current_table = stack.pop()
                    if current_table not in visited:
                        visited.add(current_table)
                        cluster_tables.append(current_table)
                        
                        # Add connected tables to stack
                        for connected_table in adjacency[current_table]:
                            if connected_table not in visited:
                                stack.append(connected_table)
                
                if cluster_tables:
                    cluster_name = f"cluster_{len(clusters) + 1}"
                    clusters[cluster_name] = cluster_tables
        
        return dict(clusters)
    
    async def _calculate_data_quality_score(self, tables: List[TableInfo]) -> float:
        """
        Calculate data quality score based on schema characteristics.
        
        Args:
            tables: List of table information
            
        Returns:
            float: Data quality score (0.0 to 1.0)
        """
        if not tables:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for table in tables:
            table_score = 0.0
            table_weight = 1.0
            
            # Check for primary keys
            if table.primary_keys:
                table_score += 0.3
            
            # Check for foreign keys
            if table.foreign_keys:
                table_score += 0.2
            
            # Check for indexes
            if table.indexes:
                table_score += 0.2
            
            # Check for column descriptions
            columns_with_descriptions = sum(1 for col in table.columns if col.description)
            if columns_with_descriptions > 0:
                table_score += 0.2 * (columns_with_descriptions / len(table.columns))
            
            # Check for proper data types
            proper_types = sum(1 for col in table.columns 
                             if col.data_type and col.data_type.lower() not in ['text', 'blob'])
            if proper_types > 0:
                table_score += 0.1 * (proper_types / len(table.columns))
            
            total_score += table_score * table_weight
            total_weight += table_weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    async def _calculate_complexity_score(self, tables: List[TableInfo], 
                                        relationships: List[RelationshipInfo]) -> float:
        """
        Calculate schema complexity score.
        
        Args:
            tables: List of table information
            relationships: List of relationship information
            
        Returns:
            float: Complexity score (0.0 to 1.0)
        """
        if not tables:
            return 0.0
        
        # Base complexity from table count
        table_complexity = min(len(tables) / 50.0, 1.0)  # Normalize to 50 tables max
        
        # Relationship complexity
        relationship_complexity = min(len(relationships) / 100.0, 1.0)  # Normalize to 100 relationships max
        
        # Column complexity
        total_columns = sum(len(table.columns) for table in tables)
        column_complexity = min(total_columns / 500.0, 1.0)  # Normalize to 500 columns max
        
        # Foreign key complexity
        total_fks = sum(len(table.foreign_keys) for table in tables)
        fk_complexity = min(total_fks / 50.0, 1.0)  # Normalize to 50 FKs max
        
        # Calculate weighted average
        complexity_score = (
            table_complexity * 0.3 +
            relationship_complexity * 0.3 +
            column_complexity * 0.2 +
            fk_complexity * 0.2
        )
        
        return min(complexity_score, 1.0)
    
    async def get_table_recommendations(self, table: TableInfo) -> List[str]:
        """
        Get recommendations for a specific table.
        
        Args:
            table: Table information
            
        Returns:
            List: Recommendations
        """
        recommendations = []
        
        # Check for missing primary key
        if not table.primary_keys:
            recommendations.append("Consider adding a primary key for better data integrity")
        
        # Check for missing indexes
        if not table.indexes:
            recommendations.append("Consider adding indexes for frequently queried columns")
        
        # Check for missing foreign keys
        if not table.foreign_keys:
            recommendations.append("Consider adding foreign key constraints for data integrity")
        
        # Check for missing column descriptions
        columns_without_descriptions = [col for col in table.columns if not col.description]
        if columns_without_descriptions:
            recommendations.append(f"Add descriptions for {len(columns_without_descriptions)} columns")
        
        # Check for large tables
        if table.row_count > 1000000:  # 1 million rows
            recommendations.append("Consider partitioning for large table performance")
        
        # Check for wide tables
        if len(table.columns) > 50:
            recommendations.append("Consider normalizing wide table")
        
        return recommendations
    
    async def generate_schema_documentation(self, analysis: SchemaAnalysis) -> str:
        """
        Generate comprehensive schema documentation.
        
        Args:
            analysis: Schema analysis result
            
        Returns:
            str: Generated documentation
        """
        doc = f"""# Database Schema Documentation

## Overview
- **Database**: {analysis.database_name}
- **Type**: {analysis.database_type.value}
- **Tables**: {analysis.total_tables}
- **Columns**: {analysis.total_columns}
- **Relationships**: {analysis.total_relationships}
- **Data Quality Score**: {analysis.data_quality_score:.2f}/1.0
- **Complexity Score**: {analysis.complexity_score:.2f}/1.0

## Business Domains
"""
        
        for domain, tables in analysis.business_domains.items():
            doc += f"\n### {domain.value.title()}\n"
            doc += f"Tables: {', '.join(tables)}\n"
        
        doc += "\n## Table Clusters\n"
        for cluster_name, tables in analysis.table_clusters.items():
            doc += f"\n### {cluster_name}\n"
            doc += f"Tables: {', '.join(tables)}\n"
        
        doc += "\n## Relationships\n"
        for rel in analysis.relationships:
            doc += f"- {rel.source_table} -> {rel.target_table} ({rel.relationship_type.value})\n"
        
        doc += f"\n## Metadata\n"
        for key, value in analysis.metadata.items():
            doc += f"- {key}: {value}\n"
        
        return doc
    
    async def clear_cache(self):
        """Clear analysis cache."""
        self._analysis_cache.clear()
        self._relationship_cache.clear()
        logger.info("Schema analysis cache cleared")


# Global schema introspector instance
_schema_introspector: Optional[SchemaIntrospector] = None


def get_schema_introspector() -> SchemaIntrospector:
    """
    Get the global schema introspector instance.
    
    Returns:
        SchemaIntrospector: Global schema introspector
    """
    global _schema_introspector
    if _schema_introspector is None:
        _schema_introspector = SchemaIntrospector()
    return _schema_introspector
