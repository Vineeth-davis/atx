# api/routes/logs.py
# Query logs and debugging endpoints

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from db.connection import SessionLocal
from db.models import QueryLog as QueryLogModel
from api.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

class QueryLog(BaseModel):
    id: str
    query_id: str
    question: str
    sql: str
    answer: str
    confidence: float
    execution_time_ms: float
    context_used: List[Dict[str, Any]]
    validation_result: Dict[str, Any]
    user_id: Optional[str] = None
    timestamp: datetime
    error: Optional[str] = None

class QueryLogsResponse(BaseModel):
    logs: List[QueryLog]
    total: int
    limit: int
    offset: int

@router.get("/", response_model=QueryLogsResponse)
async def get_logs(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user_id: Optional[str] = Query(None),
    error_only: bool = Query(False)
):
    """Get recent query logs with filtering options"""
    try:
        with SessionLocal() as session:
            query = session.query(QueryLogModel)
            
            # Filter by user ID if provided
            if user_id:
                query = query.filter(QueryLogModel.user_id == user_id)
            
            # Filter for errors only if requested
            if error_only:
                query = query.filter(QueryLogModel.error.isnot(None))
            
            # Get total count
            total = query.count()
            
            # Get paginated results
            logs = query.order_by(QueryLogModel.timestamp.desc()).offset(offset).limit(limit).all()
            
            # Convert to response format
            log_responses = []
            for log in logs:
                # Parse JSON strings back to objects
                context_used = []
                validation_result = {}
                
                try:
                    if log.context_used:
                        context_used = json.loads(log.context_used) if isinstance(log.context_used, str) else log.context_used
                except (json.JSONDecodeError, TypeError):
                    context_used = []
                
                try:
                    if log.validation_result:
                        validation_result = json.loads(log.validation_result) if isinstance(log.validation_result, str) else log.validation_result
                except (json.JSONDecodeError, TypeError):
                    validation_result = {}
                
                log_responses.append(QueryLog(
                    id=str(log.id),
                    query_id=log.query_id,
                    question=log.question,
                    sql=log.sql_query,
                    answer=log.answer or "",
                    confidence=log.confidence or 0.0,
                    execution_time_ms=log.execution_time_ms or 0.0,
                    context_used=context_used,
                    validation_result=validation_result,
                    user_id=log.user_id,
                    timestamp=log.timestamp,
                    error=log.error
                ))
            
            logger.info(f"Retrieved {len(log_responses)} logs", extra={
                'total_logs': total,
                'limit': limit,
                'offset': offset,
                'user_id': user_id,
                'error_only': error_only
            })
            
            return QueryLogsResponse(
                logs=log_responses,
                total=total,
                limit=limit,
                offset=offset
            )
            
    except Exception as e:
        logger.error(f"Error retrieving logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")

@router.get("/{query_id}", response_model=QueryLog)
async def get_log_by_query_id(query_id: str):
    """Get specific log entry by query ID"""
    try:
        with SessionLocal() as session:
            log = session.query(QueryLogModel).filter(QueryLogModel.query_id == query_id).first()
            
            if not log:
                raise HTTPException(status_code=404, detail="Log not found")
            
            logger.info(f"Retrieved log for query_id: {query_id}")
            
            # Parse JSON strings back to objects
            context_used = []
            validation_result = {}
            
            try:
                if log.context_used:
                    context_used = json.loads(log.context_used) if isinstance(log.context_used, str) else log.context_used
            except (json.JSONDecodeError, TypeError):
                context_used = []
            
            try:
                if log.validation_result:
                    validation_result = json.loads(log.validation_result) if isinstance(log.validation_result, str) else log.validation_result
            except (json.JSONDecodeError, TypeError):
                validation_result = {}
            
            return QueryLog(
                id=str(log.id),
                query_id=log.query_id,
                question=log.question,
                sql=log.sql_query,
                answer=log.answer or "",
                confidence=log.confidence or 0.0,
                execution_time_ms=log.execution_time_ms or 0.0,
                context_used=context_used,
                validation_result=validation_result,
                user_id=log.user_id,
                timestamp=log.timestamp,
                error=log.error
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving log for query_id {query_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve log")

@router.get("/stats/summary")
async def get_log_stats():
    """Get summary statistics of query logs"""
    try:
        with SessionLocal() as session:
            total_queries = session.query(QueryLogModel).count()
            successful_queries = session.query(QueryLogModel).filter(QueryLogModel.error.is_(None)).count()
            failed_queries = session.query(QueryLogModel).filter(QueryLogModel.error.isnot(None)).count()
            
            # Average execution time
            avg_execution_time = session.query(QueryLogModel.execution_time_ms).filter(
                QueryLogModel.execution_time_ms.isnot(None)
            ).all()
            avg_time = sum([t[0] for t in avg_execution_time]) / len(avg_execution_time) if avg_execution_time else 0
            
            # Recent activity (last 24 hours)
            from datetime import timedelta
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_queries = session.query(QueryLogModel).filter(
                QueryLogModel.timestamp >= recent_cutoff
            ).count()
            
            stats = {
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "failed_queries": failed_queries,
                "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                "average_execution_time_ms": round(avg_time, 2),
                "recent_queries_24h": recent_queries
            }
            
            logger.info("Retrieved log statistics", extra=stats)
            
            return stats
            
    except Exception as e:
        logger.error(f"Error retrieving log statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve log statistics")
