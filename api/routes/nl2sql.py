"""
api/routes/nl2sql.py

Endpoints for Natural Language → SQL with selectable database connections.
Ensures isolation across datasets by requiring an explicit connection name.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from core.connection_manager import get_connection_manager
from adapters.database_adapter import DatabaseSchema, TableInfo, ColumnInfo, DatabaseType
from rag.nl2sql import NL2SQLGenerator
from rag.advanced_sql_generator import AdvancedSQLGenerator

logger = logging.getLogger(__name__)
router = APIRouter()


class NL2SQLRequest(BaseModel):
    question: str
    connection: str  # e.g., "puma"
    mode: str = "auto"  # basic | advanced | auto
    execute: bool = True
    preview_rows: int = 20
    user_id: Optional[str] = None


class NL2SQLResponse(BaseModel):
    query_id: str
    connection: str
    database_type: str
    sql: str
    explanation: str
    confidence: float
    validation: Dict[str, Any]
    features_used: Optional[str] = ""
    complexity_analysis: Dict[str, Any] = {}
    executed: bool = False
    row_count: int = 0
    data_preview: List[Dict[str, Any]] = []
    execution_time_ms: float = 0.0
    timestamp: str


def _schema_to_context(schema: DatabaseSchema, max_tables: int = 50, max_columns_per_table: int = 25) -> List[Dict[str, Any]]:
    """Convert DatabaseSchema → compact context docs for NL→SQL."""
    context: List[Dict[str, Any]] = []
    tables: List[TableInfo] = schema.tables[:max_tables]
    for table in tables:
        # Table overview
        context.append({
            'type': 'table',
            'table': f"{table.schema}.{table.name}",
            'description': table.description or f"Table {table.schema}.{table.name}",
        })
        # Columns
        for col in table.columns[:max_columns_per_table]:
            context.append({
                'type': 'column',
                'table': f"{table.schema}.{table.name}",
                'column': col.name,
                'description': col.description or f"{col.data_type}{' not null' if not col.is_nullable else ''}",
            })
    return context


@router.post("/generate", response_model=NL2SQLResponse)
async def generate_sql(req: NL2SQLRequest):
    try:
        cm = get_connection_manager()
        adapter = await cm.get_connection(req.connection)
        if not adapter:
            raise HTTPException(status_code=400, detail=f"Connection '{req.connection}' is not available")

        # Get schema and convert to LLM context
        schema = await adapter.get_schema()
        context = _schema_to_context(schema)

        # Choose generator with proper namespace and dialect
        namespace = f"{req.connection}_{adapter.database_type.value}"
        dialect = adapter.database_type.value
        basic_gen = NL2SQLGenerator(namespace=namespace, dialect=dialect)
        adv_gen = AdvancedSQLGenerator(namespace=namespace, dialect=dialect)

        # Auto mode: quick heuristic on question length/keywords
        mode = req.mode.lower()
        use_advanced = False
        if mode == "advanced":
            use_advanced = True
        elif mode == "auto":
            q = req.question.lower()
            advanced_indicators = [
                'rank', 'top', 'window', 'over(', 'dense_rank', 'row_number', 'cte', 'with ',
                'percentile', 'variance', 'stddev', 'lag', 'lead', 'partition by', 'case when',
                'exists', 'not in', 'all ', ' any ', ' subquery', 'recursive'
            ]
            use_advanced = any(k in q for k in advanced_indicators) or len(req.question) > 180

        # Generate SQL
        if use_advanced:
            gen_result = await adv_gen.generate_advanced_sql(req.question, context)
            sql = gen_result.get('sql', '')
            explanation = gen_result.get('explanation', '')
            confidence = float(gen_result.get('confidence', 0.0) or 0.0)
            validation = gen_result.get('validation', {})
            features_used = gen_result.get('features_used', '')
            complexity = gen_result.get('complexity_analysis', {})
            generator_type = 'advanced'
        else:
            gen_result = await basic_gen.generate_sql(req.question, context)
            sql = gen_result.get('sql', '')
            explanation = gen_result.get('explanation', '')
            confidence = float(gen_result.get('confidence', 0.0) or 0.0)
            validation = gen_result.get('validation', {})
            features_used = ''
            complexity = {}
            generator_type = 'basic'

        if not sql:
            raise HTTPException(status_code=422, detail="Failed to generate SQL from the question")

        # Safety: disallow DDL/DML and ensure read-only
        sql_upper = sql.strip().upper()
        forbidden = ["DROP ", "DELETE ", "UPDATE ", "INSERT ", "ALTER ", "TRUNCATE ", "MERGE ", "EXEC "]
        if any(k in sql_upper for k in forbidden):
            raise HTTPException(status_code=400, detail="Generated SQL contains non-read-only operations")

        executed = False
        row_count = 0
        data_preview: List[Dict[str, Any]] = []
        exec_ms = 0.0

        if req.execute:
            start = datetime.utcnow()
            result = await adapter.execute_query(sql)
            exec_ms = (datetime.utcnow() - start).total_seconds() * 1000.0
            executed = True
            row_count = int(result.row_count)
            if result.data:
                data_preview = result.data[: max(1, min(req.preview_rows, 50))]

        return NL2SQLResponse(
            query_id=f"nl2sql_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
            connection=req.connection,
            database_type=adapter.database_type.value,
            sql=sql,
            explanation=explanation,
            confidence=confidence,
            validation=validation,
            features_used=features_used,
            complexity_analysis=complexity,
            executed=executed,
            row_count=row_count,
            data_preview=data_preview,
            execution_time_ms=exec_ms,
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"NL2SQL error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AddConnectionRequest(BaseModel):
    name: str
    database_type: DatabaseType
    config: Dict[str, Any]


@router.get("/connections")
async def list_connections():
    cm = get_connection_manager()
    return await cm.list_connections()


@router.post("/connections/add")
async def add_connection(req: AddConnectionRequest):
    cm = get_connection_manager()
    from adapters.sqlserver_adapter import SQLServerAdapter
    # Register known adapters (idempotent).
    try:
        cm.register_adapter(DatabaseType.SQLSERVER, SQLServerAdapter)
    except Exception:
        pass
    from adapters.database_adapter import ConnectionConfig
    cfg = ConnectionConfig(**req.config)
    await cm.add_connection(req.name, req.database_type, cfg, auto_connect=True)
    return {"status": "ok"}


