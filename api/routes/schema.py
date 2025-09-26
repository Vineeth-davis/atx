# api/routes/schema.py
# Database schema information endpoints

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from sqlalchemy import text, inspect
from sqlalchemy.orm import sessionmaker
from db.connection import SessionLocal, engine
from db.models import Entity, FinancialIncome, FinancialBalance, Transaction, CRMCompany, CRMActivity, QueryLog
from api.logging_config import get_logger
import json

router = APIRouter()
logger = get_logger(__name__)

@router.get("/")
async def get_schema():
    """Get comprehensive database schema information"""
    try:
        with SessionLocal() as session:
            # Get table information
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            schema_info = {
                "tables": [],
                "relationships": [],
                "total_tables": len(tables),
                "total_rows": 0,
                "database_info": {
                    "engine": str(engine.url).split('@')[1] if '@' in str(engine.url) else "local",
                    "dialect": engine.dialect.name
                }
            }
            
            # Get detailed table information
            for table_name in tables:
                table_info = await _get_table_info(session, table_name)
                schema_info["tables"].append(table_info)
                schema_info["total_rows"] += table_info.get("row_count", 0)
            
            # Get relationships
            schema_info["relationships"] = await _get_relationships()
            
            logger.info(f"Retrieved schema information for {len(tables)} tables", extra={
                'total_tables': len(tables),
                'total_rows': schema_info["total_rows"]
            })
            
            return schema_info
            
    except Exception as e:
        logger.error(f"Error retrieving schema: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schema: {str(e)}")

@router.get("/tables")
async def get_tables():
    """Get list of all tables with basic stats"""
    try:
        with SessionLocal() as session:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            table_list = []
            for table_name in tables:
                table_info = await _get_table_info(session, table_name)
                table_list.append({
                    "name": table_name,
                    "row_count": table_info.get("row_count", 0),
                    "column_count": len(table_info.get("columns", [])),
                    "description": table_info.get("description", "")
                })
            
            logger.info(f"Retrieved table list with {len(tables)} tables")
            
            return {
                "tables": table_list,
                "total_tables": len(tables)
            }
            
    except Exception as e:
        logger.error(f"Error retrieving tables: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tables: {str(e)}")

@router.get("/tables/{table_name}")
async def get_table_details(table_name: str):
    """Get detailed information about a specific table"""
    try:
        with SessionLocal() as session:
            # Check if table exists
            inspector = inspect(engine)
            if table_name not in inspector.get_table_names():
                raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
            
            table_info = await _get_table_info(session, table_name)
            
            # Get sample data
            sample_data = await _get_sample_data(session, table_name, limit=5)
            table_info["sample_data"] = sample_data
            
            logger.info(f"Retrieved details for table: {table_name}", extra={
                'table_name': table_name,
                'row_count': table_info.get("row_count", 0),
                'column_count': len(table_info.get("columns", []))
            })
            
            return table_info
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving table details for {table_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve table details: {str(e)}")

async def _get_table_info(session, table_name: str) -> Dict[str, Any]:
    """Get detailed information about a table"""
    try:
        inspector = inspect(engine)
        
        # Get columns
        columns = inspector.get_columns(table_name)
        column_info = []
        
        for col in columns:
            column_info.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col["nullable"],
                "primary_key": col.get("primary_key", False),
                "default": str(col.get("default", "")) if col.get("default") else None
            })
        
        # Get row count
        row_count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        row_count = row_count_result.scalar()
        
        # Get table description based on model
        description = _get_table_description(table_name)
        
        return {
            "name": table_name,
            "description": description,
            "columns": column_info,
            "row_count": row_count,
            "primary_keys": [col["name"] for col in column_info if col["primary_key"]],
            "foreign_keys": _get_foreign_keys(table_name)
        }
        
    except Exception as e:
        logger.error(f"Error getting table info for {table_name}: {e}")
        return {
            "name": table_name,
            "description": "Error retrieving table information",
            "columns": [],
            "row_count": 0,
            "primary_keys": [],
            "foreign_keys": []
        }

async def _get_sample_data(session, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get sample data from a table"""
    try:
        result = session.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
        columns = result.keys()
        rows = result.fetchall()
        
        sample_data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # Convert non-serializable types
                if hasattr(value, 'isoformat'):  # datetime
                    value = value.isoformat()
                elif hasattr(value, '__dict__'):  # UUID or other objects
                    value = str(value)
                row_dict[col] = value
            sample_data.append(row_dict)
        
        return sample_data
        
    except Exception as e:
        logger.error(f"Error getting sample data for {table_name}: {e}")
        return []

def _get_table_description(table_name: str) -> str:
    """Get human-readable description of a table"""
    descriptions = {
        "entities": "Companies, funds, and other business entities with basic information like industry, country, and metadata",
        "financial_income": "Income statement data with time-series financial metrics including revenue, expenses, and net income",
        "financial_balance": "Balance sheet data with time-series asset, liability, and equity information",
        "transactions": "Financial transaction events including investments, dividends, and other monetary activities",
        "crm_companies": "CRM system companies with contact information and business details",
        "crm_activities": "CRM activities and interactions with companies including calls, emails, and meetings",
        "query_logs": "System query logs for debugging, monitoring, and observability purposes"
    }
    return descriptions.get(table_name, f"Table containing {table_name} data")

def _get_foreign_keys(table_name: str) -> List[Dict[str, str]]:
    """Get foreign key relationships for a table"""
    try:
        inspector = inspect(engine)
        foreign_keys = inspector.get_foreign_keys(table_name)
        
        fk_info = []
        for fk in foreign_keys:
            fk_info.append({
                "column": fk["constrained_columns"][0] if fk["constrained_columns"] else "",
                "referenced_table": fk["referred_table"],
                "referenced_column": fk["referred_columns"][0] if fk["referred_columns"] else ""
            })
        
        return fk_info
        
    except Exception as e:
        logger.error(f"Error getting foreign keys for {table_name}: {e}")
        return []

async def _get_relationships() -> List[Dict[str, Any]]:
    """Get all table relationships"""
    relationships = [
        {
            "from_table": "financial_income",
            "from_column": "entity_id",
            "to_table": "entities",
            "to_column": "id",
            "relationship_type": "one_to_many",
            "description": "Each entity can have multiple income statements"
        },
        {
            "from_table": "financial_balance",
            "from_column": "entity_id",
            "to_table": "entities",
            "to_column": "id",
            "relationship_type": "one_to_many",
            "description": "Each entity can have multiple balance sheets"
        },
        {
            "from_table": "transactions",
            "from_column": "entity_id",
            "to_table": "entities",
            "to_column": "id",
            "relationship_type": "one_to_many",
            "description": "Each entity can have multiple transactions"
        },
        {
            "from_table": "crm_activities",
            "from_column": "company_id",
            "to_table": "crm_companies",
            "to_column": "id",
            "relationship_type": "one_to_many",
            "description": "Each CRM company can have multiple activities"
        }
    ]
    
    return relationships
