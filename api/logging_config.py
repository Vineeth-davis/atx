# api/logging_config.py
# Comprehensive logging configuration for the Atrean RAG Platform

import logging
import logging.config
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from api.config import settings

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Create structured log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        # Add trace ID if available
        if hasattr(record, 'trace_id'):
            log_entry['trace_id'] = record.trace_id
        
        # Add query ID if available
        if hasattr(record, 'query_id'):
            log_entry['query_id'] = record.query_id
        
        # Add user ID if available
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        # Add execution time if available
        if hasattr(record, 'execution_time_ms'):
            log_entry['execution_time_ms'] = record.execution_time_ms
        
        # Add error details if available
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m', # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{level_color}{record.levelname}{self.RESET}"
        
        # Format the message
        formatted = super().format(record)
        
        # Add request/trace IDs if available
        extra_info = []
        if hasattr(record, 'request_id'):
            extra_info.append(f"[REQ:{record.request_id}]")
        if hasattr(record, 'trace_id'):
            extra_info.append(f"[TRACE:{record.trace_id}]")
        if hasattr(record, 'query_id'):
            extra_info.append(f"[QUERY:{record.query_id}]")
        
        if extra_info:
            formatted = f"{' '.join(extra_info)} {formatted}"
        
        return formatted

def setup_logging():
    """Setup comprehensive logging configuration"""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Logging configuration
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'structured': {
                '()': StructuredFormatter,
            },
            'colored': {
                '()': ColoredFormatter,
                'format': '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'detailed': {
                'format': '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'colored',
                'stream': sys.stdout,
            },
            'file_app': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': log_level,
                'formatter': 'structured',
                'filename': 'logs/app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8',
            },
            'file_errors': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'structured',
                'filename': 'logs/errors.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8',
            },
            'file_queries': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'structured',
                'filename': 'logs/queries.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'encoding': 'utf-8',
            },
        },
        'loggers': {
            '': {  # Root logger
                'level': log_level,
                'handlers': ['console', 'file_app'],
                'propagate': False,
            },
            'api': {
                'level': log_level,
                'handlers': ['console', 'file_app'],
                'propagate': False,
            },
            'agents': {
                'level': log_level,
                'handlers': ['console', 'file_app'],
                'propagate': False,
            },
            'rag': {
                'level': log_level,
                'handlers': ['console', 'file_app'],
                'propagate': False,
            },
            'db': {
                'level': log_level,
                'handlers': ['console', 'file_app'],
                'propagate': False,
            },
            'query_logger': {
                'level': 'INFO',
                'handlers': ['file_queries'],
                'propagate': False,
            },
            'error_logger': {
                'level': 'ERROR',
                'handlers': ['file_errors'],
                'propagate': False,
            },
        },
    }
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("🔧 Logging system initialized", extra={
        'log_level': settings.LOG_LEVEL,
        'debug_mode': settings.DEBUG,
        'app_name': settings.APP_NAME,
        'app_version': settings.APP_VERSION
    })

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)

def log_query(
    query_id: str,
    question: str,
    sql: str,
    answer: str,
    execution_time_ms: float,
    user_id: Optional[str] = None,
    context_used: Optional[list] = None,
    validation_result: Optional[dict] = None,
    error: Optional[str] = None,
    enrichment_data: Optional[dict] = None
):
    """Log a query execution with structured data"""
    logger = logging.getLogger('query_logger')
    
    log_data = {
        'query_id': query_id,
        'question': question,
        'sql': sql,
        'answer_preview': answer[:200] + '...' if len(answer) > 200 else answer,
        'execution_time_ms': execution_time_ms,
        'user_id': user_id,
        'context_used': context_used or [],
        'validation_result': validation_result or {},
        'error': error,
        'enrichment_enabled': enrichment_data is not None,
        'enrichment_sources': list(enrichment_data.keys()) if enrichment_data else [],
    }
    
    if error:
        logger.error(f"Query execution failed: {error}", extra=log_data)
    else:
        logger.info(f"Query executed successfully", extra=log_data)

def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None
):
    """Log an error with structured context"""
    logger = logging.getLogger('error_logger')
    
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context or {},
        'request_id': request_id,
        'trace_id': trace_id,
    }
    
    logger.error(f"Error occurred: {error}", extra=error_data, exc_info=True)

def log_performance(
    operation: str,
    duration_ms: float,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
):
    """Log performance metrics"""
    logger = logging.getLogger('api')
    
    perf_data = {
        'operation': operation,
        'duration_ms': duration_ms,
        'details': details or {},
        'request_id': request_id,
    }
    
    logger.info(f"Performance: {operation} completed in {duration_ms:.2f}ms", extra=perf_data)
