# rag/retriever.py
# Semantic retrieval for schema and context

from typing import List, Dict, Any, Optional
from rag.vector_store import VectorStore, create_vector_store
from rag.embeddings import embedding_service
from db.models import Entity, FinancialIncome, FinancialBalance, Transaction, CRMCompany, CRMActivity
from db.connection import SessionLocal
import logging
import asyncio

logger = logging.getLogger(__name__)

class SchemaRetriever:
    """Retrieves relevant schema information based on user questions.

    Adapter-aware and namespaced so each external database (e.g., Puma SQL Server)
    has isolated schema documents and FAISS index.
    """
    
    def __init__(self, namespace: str = "default"):
        self.namespace = namespace
        self.vector_store = create_vector_store(namespace=self.namespace)
        self.embedding_service = embedding_service
        self.schema_documents = []
    
    async def retrieve_schema_context(self, question: str, k: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve relevant schema context for a question
        
        Args:
            question: User's natural language question
            k: Number of context items to retrieve
            
        Returns:
            List of relevant schema context items
        """
        try:
            # Generate embedding for the question
            query_embedding = await self.embedding_service.generate_single_embedding(question)
            
            if not query_embedding:
                logger.warning("Failed to generate embedding for question")
                return []
            
            # Search vector store for relevant schema docs
            results = self.vector_store.search(query_embedding, k=k)
            
            # Extract and format context
            context_items = []
            for result in results:
                metadata = result['metadata']
                context_items.append({
                    'type': metadata.get('type', 'unknown'),
                    'table': metadata.get('table', ''),
                    'column': metadata.get('column', ''),
                    'description': metadata.get('description', ''),
                    'sample_values': metadata.get('sample_values', []),
                    'relevance_score': result['score']
                })
            
            logger.info(f"Retrieved {len(context_items)} schema context items")
            return context_items
            
        except Exception as e:
            logger.error(f"Error retrieving schema context: {e}")
            return []
    
    async def retrieve_table_context(self, table_names: List[str]) -> Dict[str, Any]:
        """
        Retrieve detailed context for specific tables
        
        Args:
            table_names: List of table names to get context for
            
        Returns:
            Dictionary mapping table names to their context
        """
        context = {}
        
        try:
            with SessionLocal() as session:
                for table_name in table_names:
                    table_context = await self._get_table_details(table_name, session)
                    if table_context:
                        context[table_name] = table_context
                        
        except Exception as e:
            logger.error(f"Error retrieving table context: {e}")
            
        return context
    
    async def _get_table_details(self, table_name: str, session) -> Dict[str, Any]:
        """Get detailed information about a specific table"""
        try:
            # Map table names to models
            model_mapping = {
                'entities': Entity,
                'financial_income': FinancialIncome,
                'financial_balance': FinancialBalance,
                'transactions': Transaction,
                'crm_companies': CRMCompany,
                'crm_activities': CRMActivity
            }
            
            model = model_mapping.get(table_name)
            if not model:
                return None
            
            # Get column information
            columns = []
            for column in model.__table__.columns:
                columns.append({
                    'name': column.name,
                    'type': str(column.type),
                    'nullable': column.nullable,
                    'primary_key': column.primary_key
                })
            
            # Get sample data (first 5 rows)
            sample_data = []
            try:
                sample_rows = session.query(model).limit(5).all()
                for row in sample_rows:
                    row_dict = {}
                    for column in model.__table__.columns:
                        value = getattr(row, column.name)
                        row_dict[column.name] = str(value) if value is not None else None
                    sample_data.append(row_dict)
            except Exception as e:
                logger.warning(f"Could not fetch sample data for {table_name}: {e}")
            
            # Get row count
            try:
                row_count = session.query(model).count()
            except Exception as e:
                logger.warning(f"Could not get row count for {table_name}: {e}")
                row_count = 0
            
            return {
                'table_name': table_name,
                'columns': columns,
                'sample_data': sample_data,
                'row_count': row_count,
                'description': self._get_table_description(table_name)
            }
            
        except Exception as e:
            logger.error(f"Error getting table details for {table_name}: {e}")
            return None
    
    def _get_table_description(self, table_name: str) -> str:
        """Get human-readable description of a table"""
        descriptions = {
            'entities': 'Companies, funds, and other business entities with basic information',
            'financial_income': 'Income statement data including revenue, costs, and profit metrics',
            'financial_balance': 'Balance sheet data including assets, liabilities, and equity',
            'transactions': 'Individual financial transactions and movements',
            'crm_companies': 'Customer relationship management data for companies',
            'crm_activities': 'CRM activities and interactions with companies'
        }
        return descriptions.get(table_name, f'Table containing {table_name} data')
    
    async def build_schema_documents(self, adapter=None):
        """Build schema documents for vector indexing from adapter or demo data."""
        try:
            logger.info(f"Building schema documents for namespace: {self.namespace}")
            
            documents = []
            metadata_list = []
            
            if adapter and hasattr(adapter, 'get_schema'):
                # Build from real adapter schema
                logger.info("Building schema documents from adapter...")
                schema = await adapter.get_schema()
                
                for table in schema.tables[:50]:  # Limit to 50 tables
                    # Table overview document
                    table_doc = f"Table: {table.schema}.{table.name}"
                    if table.description:
                        table_doc += f"\nDescription: {table.description}"
                    if table.business_domain:
                        table_doc += f"\nBusiness Domain: {table.business_domain}"
                    
                    # Add column information
                    column_info = []
                    for col in table.columns[:25]:  # Limit to 25 columns per table
                        col_desc = f"{col.name} ({col.data_type}"
                        if col.is_primary_key:
                            col_desc += ", primary key"
                        if col.is_foreign_key:
                            col_desc += ", foreign key"
                        col_desc += ")"
                        column_info.append(col_desc)
                    
                    if column_info:
                        table_doc += f"\nColumns: {', '.join(column_info)}"
                    
                    documents.append(table_doc)
                    metadata_list.append({
                        'type': 'table',
                        'table': f"{table.schema}.{table.name}",
                        'description': table.description or f"Table {table.schema}.{table.name}",
                        'business_domain': table.business_domain or 'general',
                        'row_count': table.row_count,
                        'namespace': self.namespace
                    })
                    
                    # Individual column documents for better retrieval
                    for col in table.columns[:25]:
                        # Create more searchable column document
                        col_doc = f"Table: {table.schema}.{table.name}\nColumn: {col.name}\nType: {col.data_type}"
                        
                        # Add table context to make it more searchable
                        table_name_lower = table.name.lower()
                        if 'vendor' in table_name_lower:
                            col_doc += f"\nThis is a vendor-related column in the {table.name} table"
                        elif 'purchase' in table_name_lower:
                            col_doc += f"\nThis is a purchase-related column in the {table.name} table"
                        elif 'order' in table_name_lower:
                            col_doc += f"\nThis is an order-related column in the {table.name} table"
                        
                        if col.description:
                            col_doc += f"\nDescription: {col.description}"
                        if col.is_primary_key:
                            col_doc += "\nPrimary Key: Yes"
                        if col.is_foreign_key:
                            col_doc += "\nForeign Key: Yes"
                        if not col.is_nullable:
                            col_doc += "\nNullable: No"
                        
                        documents.append(col_doc)
                        metadata_list.append({
                            'type': 'column',
                            'table': f"{table.schema}.{table.name}",
                            'column': col.name,
                            'data_type': col.data_type,
                            'description': col.description or f"{col.data_type} column",
                            'is_primary_key': col.is_primary_key,
                            'is_foreign_key': col.is_foreign_key,
                            'namespace': self.namespace
                        })
            else:
                # Fallback to demo data
                logger.info("Building schema documents from demo data...")
                with SessionLocal() as session:
                    tables = ['entities', 'financial_income', 'financial_balance', 'transactions', 'crm_companies', 'crm_activities']
                    
                    for table_name in tables:
                        table_context = await self._get_table_details(table_name, session)
                        if table_context:
                            # Create document for table overview
                            table_doc = f"Table: {table_name}\nDescription: {table_context['description']}\nColumns: {', '.join([col['name'] for col in table_context['columns']])}"
                            documents.append(table_doc)
                            metadata_list.append({
                                'type': 'table',
                                'table': table_name,
                                'description': table_context['description'],
                                'row_count': table_context['row_count'],
                                'namespace': self.namespace
                            })
                            
                            # Create documents for each column
                            for column in table_context['columns']:
                                column_doc = f"Column: {table_name}.{column['name']}\nType: {column['type']}\nTable: {table_name}\nDescription: {self._get_column_description(table_name, column['name'])}"
                                documents.append(column_doc)
                                metadata_list.append({
                                    'type': 'column',
                                    'table': table_name,
                                    'column': column['name'],
                                    'data_type': column['type'],
                                    'description': self._get_column_description(table_name, column['name']),
                                    'namespace': self.namespace
                                })
            
            # Generate embeddings for all documents
            if documents:
                embeddings = await self.embedding_service.generate_embeddings(documents)
                
                # Add to vector store
                self.vector_store.add_vectors(embeddings, metadata_list)
                self.vector_store.save_index()
                
                logger.info(f"Built and indexed {len(documents)} schema documents")
            else:
                logger.warning("No schema documents to index")
                
        except Exception as e:
            logger.error(f"Error building schema documents: {e}")
            raise
    
    def _get_column_description(self, table_name: str, column_name: str) -> str:
        """Get human-readable description of a column"""
        descriptions = {
            'entities': {
                'name': 'Entity name or identifier',
                'type': 'Type of entity (Public, Private, etc.)',
                'industry': 'Industry sector',
                'country': 'Country of operation'
            },
            'financial_income': {
                'entity_id': 'Reference to entity',
                'date': 'Financial period date',
                'revenue': 'Total revenue amount',
                'cogs': 'Cost of goods sold',
                'gross_profit': 'Revenue minus COGS',
                'operating_expenses': 'Operating expenses',
                'net_income': 'Final net income'
            },
            'financial_balance': {
                'entity_id': 'Reference to entity',
                'date': 'Balance sheet date',
                'assets': 'Total assets',
                'liabilities': 'Total liabilities',
                'equity': 'Shareholders equity'
            },
            'transactions': {
                'entity_id': 'Reference to entity',
                'date': 'Transaction date',
                'type': 'Transaction type',
                'amount': 'Transaction amount',
                'description': 'Transaction description'
            },
            'crm_companies': {
                'name': 'Company name',
                'industry': 'Company industry',
                'contact_person': 'Primary contact person',
                'email': 'Contact email',
                'phone': 'Contact phone'
            },
            'crm_activities': {
                'company_id': 'Reference to CRM company',
                'date': 'Activity date',
                'type': 'Activity type',
                'notes': 'Activity notes'
            }
        }
        
        table_descriptions = descriptions.get(table_name, {})
        return table_descriptions.get(column_name, f'{column_name} field in {table_name} table')

class ContextRetriever:
    """Retrieves relevant data context for questions"""
    
    def __init__(self, namespace: str = "default"):
        self.vector_store = create_vector_store(namespace=namespace)
        self.embedding_service = embedding_service
    
    async def retrieve_data_context(self, question: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant data context for a question
        
        Args:
            question: User's natural language question
            k: Number of context items to retrieve
            
        Returns:
            List of relevant data context items
        """
        # TODO: Implement data context retrieval
        # Search for relevant rows, summaries, or aggregated data
        pass
    
    def build_data_documents(self):
        """Build data documents for vector indexing"""
        # TODO: Implement data document generation
        # Create documents from sample rows, summaries, aggregations
        pass
