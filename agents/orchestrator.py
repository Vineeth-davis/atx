# agents/orchestrator.py
# Multi-agent orchestration for RAG workflow

from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime
from rag.retriever import SchemaRetriever
from rag.nl2sql import NL2SQLGenerator
from rag.advanced_sql_generator import advanced_sql_generator
from rag.embeddings import embedding_service
from agents.analysis_agent import analysis_agent
from db.connection import SessionLocal
from db.models import QueryLog
import json

logger = logging.getLogger(__name__)

class RAGOrchestrator:
    """Orchestrates the RAG workflow with multiple agents"""
    
    def __init__(self):
        self.schema_retriever = SchemaRetriever()
        self.nl2sql_generator = NL2SQLGenerator()
        self.advanced_sql_generator = advanced_sql_generator
        self.embedding_service = embedding_service
        self.analysis_agent = analysis_agent
    
    def _determine_sql_generator(self, question: str) -> str:
        """
        Determine which SQL generator to use based on query complexity
        
        Args:
            question: User's natural language question
            
        Returns:
            'advanced' for complex queries, 'basic' for simple queries
        """
        # Keywords that indicate complex queries requiring advanced SQL features
        complex_indicators = [
            'rank', 'percentile', 'running total', 'cumulative', 'trend', 'growth',
            'compare across', 'between', 'relationship', 'correlation', 'correlate',
            'step by step', 'first calculate', 'then', 'intermediate', 'temporary',
            'window', 'partition by', 'over time', 'lag', 'lead', 'previous', 'next',
            'standard deviation', 'variance', 'distribution', 'statistics',
            'if', 'when', 'condition', 'categorize', 'classify', 'bucket', 'segment',
            'hierarchy', 'tree', 'parent', 'child', 'recursive'
        ]
        
        question_lower = question.lower()
        complexity_score = sum(1 for indicator in complex_indicators if indicator in question_lower)
        
        # Use advanced generator for queries with 2+ complexity indicators
        return 'advanced' if complexity_score >= 2 else 'basic'
    
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
            
            # Step 2: Determine SQL generator based on query complexity
            generator_type = self._determine_sql_generator(question)
            logger.info(f"Using {generator_type} SQL generator for query complexity")
            
            # Step 3: Generate SQL using appropriate generator
            if generator_type == 'advanced':
                sql_result = await self.advanced_sql_generator.generate_advanced_sql(question, schema_context)
            else:
                sql_result = await self.nl2sql_generator.generate_sql(question, schema_context)
            
            # Step 4: Execution Agent - Execute SQL and get results
            execution_result = await self._execute_sql(sql_result.get('sql', ''))
            
            # Step 5: Analysis Agent - Analyze and format results
            analysis_result = await self.analysis_agent.analyze_results(
                execution_result, question, sql_result, schema_context
            )
            
            # Build final response
            response = {
                'query_id': query_id,
                'question': question,
                'sql': sql_result.get('sql', ''),
                'answer': analysis_result.get('answer', ''),
                'explanation': sql_result.get('explanation', ''),
                'confidence': analysis_result.get('confidence', sql_result.get('confidence', 0.0)),
                'context_used': schema_context,
                'validation': analysis_result.get('validation', sql_result.get('validation', {})),
                'reasoning': analysis_result.get('reasoning', {}),
                'insights': analysis_result.get('insights', []),
                'data_preview': analysis_result.get('data_preview', []),
                'summary': analysis_result.get('summary', ''),
                'generator_type': generator_type,
                'features_used': sql_result.get('features_used', ''),
                'complexity_analysis': sql_result.get('complexity_analysis', {}),
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
                'reasoning': {'reasoning': f'Error occurred: {str(e)}'},
                'insights': ['Unable to generate insights due to error'],
                'data_preview': [],
                'summary': 'Processing failed',
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
        """Initialize the RAG system by building schema documents and vector index"""
        try:
            logger.info("🚀 Starting RAG system initialization...")
            
            # Check if vector store already exists and has data
            stats = self.schema_retriever.vector_store.get_stats()
            if stats['total_vectors'] > 0:
                logger.info(f"📊 Found existing vector store with {stats['total_vectors']} vectors")
                logger.info("✅ RAG system already initialized - skipping rebuild")
                return
            
            logger.info("📚 Building schema documents...")
            await self.schema_retriever.build_schema_documents()
            
            # Verify initialization
            final_stats = self.schema_retriever.vector_store.get_stats()
            logger.info(f"✅ RAG system initialized successfully!")
            logger.info(f"📈 Vector store stats: {final_stats['total_vectors']} vectors, {final_stats['dimension']} dimensions")
            
        except Exception as e:
            logger.error(f"❌ Error initializing RAG system: {e}")
            logger.error("🔧 RAG system will work with reduced functionality")
            # Don't raise the exception to allow graceful degradation
            raise

# Global instance
rag_orchestrator = RAGOrchestrator()