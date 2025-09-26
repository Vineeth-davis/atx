# agents/orchestrator.py
# Multi-agent orchestration for RAG workflow

from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime
from rag.retriever import SchemaRetriever
from rag.nl2sql import NL2SQLGenerator
from rag.embeddings import embedding_service
from db.connection import SessionLocal
from db.models import QueryLog
import json

logger = logging.getLogger(__name__)

class RAGOrchestrator:
    """Orchestrates the RAG workflow with multiple agents"""
    
    def __init__(self):
        self.schema_retriever = SchemaRetriever()
        self.nl2sql_generator = NL2SQLGenerator()
        self.embedding_service = embedding_service
    
    async def process_question(self, question: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a natural language question through the RAG workflow
        
        Args:
            question: User's natural language question
            user_id: Optional user identifier for logging
            
        Returns:
            Dictionary containing answer, SQL, context, and metadata
        """
        start_time = datetime.utcnow()
        query_id = f"query_{start_time.strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            logger.info(f"Processing question: {question[:100]}...")
            
            # Step 1: Retrieval Agent - Get relevant schema context
            schema_context = await self.schema_retriever.retrieve_schema_context(question, k=10)
            
            # Step 2: Analysis Agent - Generate SQL from question and context
            sql_result = await self.nl2sql_generator.generate_sql(question, schema_context)
            
            # Step 3: Execution Agent - Execute SQL and get results
            execution_result = await self._execute_sql(sql_result.get('sql', ''))
            
            # Step 4: Analysis Agent - Analyze and format results
            analysis_result = await self._analyze_results(execution_result, question, sql_result)
            
            # Build final response
            response = {
                'query_id': query_id,
                'question': question,
                'sql': sql_result.get('sql', ''),
                'answer': analysis_result.get('answer', ''),
                'explanation': sql_result.get('explanation', ''),
                'confidence': sql_result.get('confidence', 0.0),
                'context_used': schema_context,
                'validation': sql_result.get('validation', {}),
                'execution_time_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                'timestamp': start_time.isoformat(),
                'user_id': user_id
            }
            
            # Log the query
            await self._log_query(response)
            
            logger.info(f"Successfully processed question in {response['execution_time_ms']:.2f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            
            # Log error
            error_response = {
                'query_id': query_id,
                'question': question,
                'sql': '',
                'answer': f'Error processing question: {str(e)}',
                'explanation': 'An error occurred during processing',
                'confidence': 0.0,
                'context_used': [],
                'validation': {'valid': False, 'errors': [str(e)]},
                'execution_time_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                'timestamp': start_time.isoformat(),
                'user_id': user_id,
                'error': str(e)
            }
            
            await self._log_query(error_response)
            return error_response
    
    async def _execute_sql(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        if not sql or not sql.strip():
            return {'success': False, 'error': 'No SQL query provided', 'data': []}
        
        try:
            from sqlalchemy import text
            with SessionLocal() as session:
                # Execute the SQL query using text() wrapper
                result = session.execute(text(sql))
                
                # Get column names
                columns = list(result.keys()) if hasattr(result, 'keys') else []
                
                # Get data rows
                rows = result.fetchall()
                data = [dict(zip(columns, row)) for row in rows] if columns else []
                
                return {
                    'success': True,
                    'data': data,
                    'columns': columns,
                    'row_count': len(data)
                }
                
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }
    
    async def _analyze_results(self, execution_result: Dict[str, Any], question: str, sql_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze execution results and generate human-readable answer"""
        try:
            if not execution_result.get('success', False):
                return {
                    'answer': f"Query execution failed: {execution_result.get('error', 'Unknown error')}",
                    'summary': 'Unable to execute the generated SQL query'
                }
            
            data = execution_result.get('data', [])
            row_count = execution_result.get('row_count', 0)
            
            if row_count == 0:
                return {
                    'answer': 'No data found matching your criteria.',
                    'summary': 'The query returned no results'
                }
            
            # Generate summary based on data
            if row_count == 1:
                # Single row result
                row = data[0]
                if len(row) == 1:
                    # Single value
                    key, value = next(iter(row.items()))
                    answer = f"The {key.replace('_', ' ')} is {value}"
                else:
                    # Multiple columns
                    answer = f"Found 1 result: {', '.join([f'{k}: {v}' for k, v in row.items()])}"
            else:
                # Multiple rows
                answer = f"Found {row_count} results"
                
                # Add summary statistics if applicable
                numeric_columns = []
                for col in execution_result.get('columns', []):
                    if any(isinstance(row.get(col), (int, float)) for row in data if row.get(col) is not None):
                        numeric_columns.append(col)
                
                if numeric_columns:
                    summary_stats = []
                    for col in numeric_columns:
                        values = [row[col] for row in data if row[col] is not None]
                        if values:
                            avg_val = sum(values) / len(values)
                            max_val = max(values)
                            min_val = min(values)
                            summary_stats.append(f"{col}: avg={avg_val:.2f}, max={max_val}, min={min_val}")
                    
                    if summary_stats:
                        answer += f". Summary: {', '.join(summary_stats)}"
            
            return {
                'answer': answer,
                'summary': f'Query returned {row_count} rows',
                'data_preview': data[:5] if len(data) > 5 else data  # Show first 5 rows
            }
            
        except Exception as e:
            logger.error(f"Error analyzing results: {e}")
            return {
                'answer': f'Error analyzing results: {str(e)}',
                'summary': 'Analysis failed'
            }
    
    async def _log_query(self, response: Dict[str, Any]):
        """Log query to database"""
        try:
            with SessionLocal() as session:
                query_log = QueryLog(
                    query_id=response.get('query_id', ''),
                    question=response.get('question', ''),
                    sql_query=response.get('sql', ''),
                    answer=response.get('answer', ''),
                    confidence=response.get('confidence', 0.0),
                    execution_time_ms=response.get('execution_time_ms', 0),
                    context_used=json.dumps(response.get('context_used', [])),
                    validation_result=json.dumps(response.get('validation', {})),
                    user_id=response.get('user_id'),
                    timestamp=datetime.utcnow(),
                    error=response.get('error')
                )
                session.add(query_log)
                session.commit()
                
        except Exception as e:
            logger.error(f"Error logging query: {e}")
    
    async def get_query_history(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get query history from database"""
        try:
            with SessionLocal() as session:
                query = session.query(QueryLog)
                
                if user_id:
                    query = query.filter(QueryLog.user_id == user_id)
                
                logs = query.order_by(QueryLog.timestamp.desc()).limit(limit).all()
                
                return [
                    {
                        'query_id': log.query_id,
                        'question': log.question,
                        'sql_query': log.sql_query,
                        'answer': log.answer,
                        'confidence': log.confidence,
                        'execution_time_ms': log.execution_time_ms,
                        'timestamp': log.timestamp.isoformat(),
                        'user_id': log.user_id,
                        'error': log.error
                    }
                    for log in logs
                ]
                
        except Exception as e:
            logger.error(f"Error getting query history: {e}")
            return []
    
    async def initialize_rag_system(self):
        """Initialize the RAG system by building schema documents"""
        try:
            logger.info("Initializing RAG system...")
            await self.schema_retriever.build_schema_documents()
            logger.info("RAG system initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAG system: {e}")
            raise

# Global instance
rag_orchestrator = RAGOrchestrator()