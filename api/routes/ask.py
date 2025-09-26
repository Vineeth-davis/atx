# api/routes/ask.py
# Main question-answering endpoint

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
from agents.orchestrator import rag_orchestrator
from api.logging_config import get_logger, log_error

logger = get_logger(__name__)
router = APIRouter()

class AskRequest(BaseModel):
    question: str
    include_sql: bool = True
    include_context: bool = True
    user_id: Optional[str] = None

class AskResponse(BaseModel):
    query_id: str
    question: str
    answer: str
    sql: str
    explanation: str
    confidence: float
    context_used: List[Dict[str, Any]]
    validation: Dict[str, Any]
    reasoning: Dict[str, Any] = {}
    insights: List[str] = []
    data_preview: List[Dict[str, Any]] = []
    summary: str = ""
    generator_type: str = "basic"
    features_used: str = ""
    complexity_analysis: Dict[str, Any] = {}
    enrichment: Dict[str, Any] = {}
    enrichment_insights: str = ""
    external_data: Dict[str, Any] = {}
    execution_time_ms: float
    timestamp: str
    user_id: Optional[str] = None

@router.post("/", response_model=AskResponse)
async def ask_question(request: AskRequest, http_request: Request):
    """
    Main endpoint for asking questions about the dataset.
    Returns answer, SQL query, and context used.
    """
    try:
        # Get request ID from middleware
        request_id = getattr(http_request.state, 'request_id', None)
        
        logger.info(f"Processing question: {request.question[:100]}...", extra={
            'request_id': request_id,
            'user_id': request.user_id,
            'include_sql': request.include_sql,
            'include_context': request.include_context
        })
        
        # Process question through RAG orchestrator
        result = await rag_orchestrator.process_question(
            question=request.question,
            user_id=request.user_id
        )
        
        # Build response
        response = AskResponse(
            query_id=result.get('query_id', ''),
            question=result.get('question', ''),
            answer=result.get('answer', ''),
            sql=result.get('sql', '') if request.include_sql else '',
            explanation=result.get('explanation', ''),
            confidence=result.get('confidence', 0.0),
            context_used=result.get('context_used', []) if request.include_context else [],
            validation=result.get('validation', {}),
            reasoning=result.get('reasoning', {}),
            insights=result.get('insights', []),
            data_preview=result.get('data_preview', []),
            summary=result.get('summary', ''),
            generator_type=result.get('generator_type', 'basic'),
            features_used=result.get('features_used', ''),
            complexity_analysis=result.get('complexity_analysis', {}),
            enrichment=result.get('enrichment', {}),
            enrichment_insights=result.get('enrichment_insights', ''),
            external_data=result.get('external_data', {}),
            execution_time_ms=result.get('execution_time_ms', 0),
            timestamp=result.get('timestamp', ''),
            user_id=result.get('user_id')
        )
        
        logger.info(f"Successfully processed question in {response.execution_time_ms:.2f}ms", extra={
            'request_id': request_id,
            'query_id': response.query_id,
            'execution_time_ms': response.execution_time_ms,
            'confidence': response.confidence,
            'enrichment_enabled': bool(response.enrichment)
        })
        
        return response
        
    except Exception as e:
        request_id = getattr(http_request.state, 'request_id', None)
        log_error(e, {
            'question': request.question,
            'user_id': request.user_id,
            'include_sql': request.include_sql,
            'include_context': request.include_context
        }, request_id)
        
        logger.error(f"Error processing question: {e}", extra={
            'request_id': request_id,
            'error': str(e)
        }, exc_info=True)
        
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@router.get("/history")
async def get_query_history(user_id: Optional[str] = None, limit: int = 50):
    """
    Get query history for a user or all users
    """
    try:
        history = await rag_orchestrator.get_query_history(user_id=user_id, limit=limit)
        return {"queries": history, "count": len(history)}
    except Exception as e:
        logger.error(f"Error getting query history: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting query history: {str(e)}")

@router.post("/initialize")
async def initialize_rag_system():
    """
    Initialize the RAG system by building schema documents
    """
    try:
        await rag_orchestrator.initialize_rag_system()
        return {"message": "RAG system initialized successfully"}
    except Exception as e:
        logger.error(f"Error initializing RAG system: {e}")
        raise HTTPException(status_code=500, detail=f"Error initializing RAG system: {str(e)}")
