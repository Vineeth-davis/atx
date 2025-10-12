"""
Connection Manager

A centralized connection management system that handles multiple database connections,
connection pooling, testing, validation, and lifecycle management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Type
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import threading
from contextlib import asynccontextmanager

from adapters.database_adapter import (
    DatabaseAdapter,
    DatabaseType,
    ConnectionConfig,
    ConnectionError,
    QueryExecutionError,
    SchemaError
)

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Connection status enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    TESTING = "testing"


@dataclass
class ConnectionInfo:
    """Information about a database connection"""
    connection_id: str
    name: str
    database_type: DatabaseType
    config: ConnectionConfig
    adapter: Optional[DatabaseAdapter] = None
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    last_tested: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    is_active: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pooling"""
    max_connections_per_type: int = 10
    max_total_connections: int = 50
    connection_timeout: int = 30
    idle_timeout: int = 300  # 5 minutes
    test_interval: int = 60  # 1 minute
    retry_attempts: int = 3
    retry_delay: int = 5  # seconds
    health_check_enabled: bool = True
    auto_reconnect: bool = True


class ConnectionManager:
    """
    Centralized connection manager for multiple database types.
    
    Features:
    - Multi-database connection management
    - Connection pooling per database type
    - Connection testing and validation
    - Health monitoring and auto-reconnection
    - Connection lifecycle management
    - Performance metrics and monitoring
    """
    
    def __init__(self, pool_config: Optional[ConnectionPoolConfig] = None):
        """
        Initialize connection manager.
        
        Args:
            pool_config: Connection pool configuration
        """
        self.pool_config = pool_config or ConnectionPoolConfig()
        self._connections: Dict[str, ConnectionInfo] = {}
        self._adapters: Dict[DatabaseType, Type[DatabaseAdapter]] = {}
        self._lock = asyncio.Lock()
        self._health_monitor_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._metrics = {
            'total_connections': 0,
            'active_connections': 0,
            'failed_connections': 0,
            'total_queries': 0,
            'total_errors': 0,
            'avg_response_time': 0.0
        }
    
    def register_adapter(self, database_type: DatabaseType, adapter_class: Type[DatabaseAdapter]):
        """
        Register a database adapter for a specific database type.
        
        Args:
            database_type: Type of database
            adapter_class: Adapter class implementation
        """
        self._adapters[database_type] = adapter_class
        logger.info(f"Registered adapter for {database_type.value}")
    
    async def add_connection(self, name: str, database_type: DatabaseType, 
                           config: ConnectionConfig, auto_connect: bool = True) -> str:
        """
        Add a new database connection.
        
        Args:
            name: Unique name for the connection
            database_type: Type of database
            config: Connection configuration
            auto_connect: Whether to connect immediately
            
        Returns:
            str: Connection ID
        """
        async with self._lock:
            if name in self._connections:
                raise ValueError(f"Connection '{name}' already exists")
            
            if database_type not in self._adapters:
                raise ValueError(f"No adapter registered for {database_type.value}")
            
            connection_id = f"{database_type.value}_{name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            connection_info = ConnectionInfo(
                connection_id=connection_id,
                name=name,
                database_type=database_type,
                config=config,
                metadata={
                    'created_by': 'connection_manager',
                    'version': '1.0.0'
                }
            )
            
            self._connections[name] = connection_info
            self._metrics['total_connections'] += 1
            
            logger.info(f"Added connection '{name}' ({database_type.value})")
            
            if auto_connect:
                await self.connect(name)
            
            return connection_id
    
    async def connect(self, name: str) -> bool:
        """
        Connect to a database.
        
        Args:
            name: Connection name
            
        Returns:
            bool: True if connection successful
        """
        if name not in self._connections:
            raise ValueError(f"Connection '{name}' not found")
        
        connection_info = self._connections[name]
        
        if connection_info.status == ConnectionStatus.CONNECTED:
            logger.info(f"Connection '{name}' already connected")
            return True
        
        try:
            connection_info.status = ConnectionStatus.CONNECTING
            
            # Create adapter instance
            adapter_class = self._adapters[connection_info.database_type]
            adapter = adapter_class(connection_info.config)
            
            # Connect
            success = await adapter.connect()
            
            if success:
                connection_info.adapter = adapter
                connection_info.status = ConnectionStatus.CONNECTED
                connection_info.is_active = True
                connection_info.last_used = datetime.utcnow()
                connection_info.error_count = 0
                connection_info.last_error = None
                
                self._metrics['active_connections'] += 1
                logger.info(f"Successfully connected to '{name}' ({connection_info.database_type.value})")
                return True
            else:
                connection_info.status = ConnectionStatus.ERROR
                connection_info.error_count += 1
                connection_info.last_error = "Connection failed"
                self._metrics['failed_connections'] += 1
                return False
                
        except Exception as e:
            connection_info.status = ConnectionStatus.ERROR
            connection_info.error_count += 1
            connection_info.last_error = str(e)
            self._metrics['failed_connections'] += 1
            logger.error(f"Failed to connect to '{name}': {e}")
            return False
    
    async def disconnect(self, name: str) -> bool:
        """
        Disconnect from a database.
        
        Args:
            name: Connection name
            
        Returns:
            bool: True if disconnection successful
        """
        if name not in self._connections:
            raise ValueError(f"Connection '{name}' not found")
        
        connection_info = self._connections[name]
        
        if connection_info.status == ConnectionStatus.DISCONNECTED:
            logger.info(f"Connection '{name}' already disconnected")
            return True
        
        try:
            if connection_info.adapter:
                await connection_info.adapter.disconnect()
            
            connection_info.adapter = None
            connection_info.status = ConnectionStatus.DISCONNECTED
            connection_info.is_active = False
            
            if connection_info.status == ConnectionStatus.CONNECTED:
                self._metrics['active_connections'] -= 1
            
            logger.info(f"Disconnected from '{name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from '{name}': {e}")
            return False
    
    async def test_connection(self, name: str) -> bool:
        """
        Test a database connection.
        
        Args:
            name: Connection name
            
        Returns:
            bool: True if connection test successful
        """
        if name not in self._connections:
            raise ValueError(f"Connection '{name}' not found")
        
        connection_info = self._connections[name]
        
        try:
            connection_info.status = ConnectionStatus.TESTING
            
            if not connection_info.adapter:
                # Try to connect first
                await self.connect(name)
            
            if connection_info.adapter:
                success = await connection_info.adapter.test_connection()
                connection_info.last_tested = datetime.utcnow()
                
                if success:
                    connection_info.status = ConnectionStatus.CONNECTED
                    connection_info.error_count = 0
                    connection_info.last_error = None
                    logger.info(f"Connection test successful for '{name}'")
                else:
                    connection_info.status = ConnectionStatus.ERROR
                    connection_info.error_count += 1
                    connection_info.last_error = "Connection test failed"
                    logger.warning(f"Connection test failed for '{name}'")
                
                return success
            else:
                connection_info.status = ConnectionStatus.ERROR
                connection_info.error_count += 1
                connection_info.last_error = "No adapter available"
                return False
                
        except Exception as e:
            connection_info.status = ConnectionStatus.ERROR
            connection_info.error_count += 1
            connection_info.last_error = str(e)
            logger.error(f"Connection test error for '{name}': {e}")
            return False
    
    async def get_connection(self, name: str) -> Optional[DatabaseAdapter]:
        """
        Get a database adapter for a connection.
        
        Args:
            name: Connection name
            
        Returns:
            DatabaseAdapter: Database adapter instance
        """
        if name not in self._connections:
            raise ValueError(f"Connection '{name}' not found")
        
        connection_info = self._connections[name]
        
        if connection_info.status != ConnectionStatus.CONNECTED:
            # Try to reconnect if auto-reconnect is enabled
            if self.pool_config.auto_reconnect:
                await self.connect(name)
        
        if connection_info.adapter and connection_info.status == ConnectionStatus.CONNECTED:
            connection_info.last_used = datetime.utcnow()
            return connection_info.adapter
        
        return None
    
    async def execute_query(self, connection_name: str, query: str, 
                           params: Optional[Dict] = None) -> Any:
        """
        Execute a query on a specific connection.
        
        Args:
            connection_name: Name of the connection
            query: SQL query
            params: Query parameters
            
        Returns:
            QueryResult: Query execution result
        """
        adapter = await self.get_connection(connection_name)
        if not adapter:
            raise ConnectionError(f"Connection '{connection_name}' not available")
        
        start_time = datetime.utcnow()
        
        try:
            result = await adapter.execute_query(query, params)
            
            # Update metrics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._metrics['total_queries'] += 1
            
            # Update average response time
            if self._metrics['avg_response_time'] == 0:
                self._metrics['avg_response_time'] = execution_time
            else:
                self._metrics['avg_response_time'] = (
                    self._metrics['avg_response_time'] * 0.9 + execution_time * 0.1
                )
            
            return result
            
        except Exception as e:
            self._metrics['total_errors'] += 1
            connection_info = self._connections[connection_name]
            connection_info.error_count += 1
            connection_info.last_error = str(e)
            raise
    
    async def get_schema(self, connection_name: str, force_refresh: bool = False) -> Any:
        """
        Get database schema for a connection.
        
        Args:
            connection_name: Name of the connection
            force_refresh: Force schema refresh
            
        Returns:
            DatabaseSchema: Database schema information
        """
        adapter = await self.get_connection(connection_name)
        if not adapter:
            raise ConnectionError(f"Connection '{connection_name}' not available")
        
        return await adapter.get_schema(force_refresh)
    
    async def remove_connection(self, name: str) -> bool:
        """
        Remove a database connection.
        
        Args:
            name: Connection name
            
        Returns:
            bool: True if removal successful
        """
        if name not in self._connections:
            raise ValueError(f"Connection '{name}' not found")
        
        connection_info = self._connections[name]
        
        # Disconnect first
        await self.disconnect(name)
        
        # Remove from connections
        del self._connections[name]
        
        if connection_info.status == ConnectionStatus.CONNECTED:
            self._metrics['active_connections'] -= 1
        
        self._metrics['total_connections'] -= 1
        
        logger.info(f"Removed connection '{name}'")
        return True
    
    async def list_connections(self) -> List[Dict[str, Any]]:
        """
        List all connections with their status.
        
        Returns:
            List[Dict]: List of connection information
        """
        connections = []
        for name, info in self._connections.items():
            connections.append({
                'name': name,
                'connection_id': info.connection_id,
                'database_type': info.database_type.value,
                'status': info.status.value,
                'is_active': info.is_active,
                'created_at': info.created_at.isoformat(),
                'last_used': info.last_used.isoformat() if info.last_used else None,
                'last_tested': info.last_tested.isoformat() if info.last_tested else None,
                'error_count': info.error_count,
                'last_error': info.last_error,
                'host': info.config.host,
                'database': info.config.database
            })
        
        return connections
    
    async def get_connection_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific connection.
        
        Args:
            name: Connection name
            
        Returns:
            Dict: Connection information
        """
        if name not in self._connections:
            return None
        
        info = self._connections[name]
        return {
            'name': name,
            'connection_id': info.connection_id,
            'database_type': info.database_type.value,
            'status': info.status.value,
            'is_active': info.is_active,
            'created_at': info.created_at.isoformat(),
            'last_used': info.last_used.isoformat() if info.last_used else None,
            'last_tested': info.last_tested.isoformat() if info.last_tested else None,
            'error_count': info.error_count,
            'last_error': info.last_error,
            'config': {
                'host': info.config.host,
                'port': info.config.port,
                'database': info.config.database,
                'username': info.config.username,
                'connection_timeout': info.config.connection_timeout,
                'pool_size': info.config.pool_size,
                'max_overflow': info.config.max_overflow
            },
            'metadata': info.metadata
        }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get connection manager metrics.
        
        Returns:
            Dict: Performance metrics
        """
        return {
            'connections': self._metrics.copy(),
            'pool_config': {
                'max_connections_per_type': self.pool_config.max_connections_per_type,
                'max_total_connections': self.pool_config.max_total_connections,
                'connection_timeout': self.pool_config.connection_timeout,
                'idle_timeout': self.pool_config.idle_timeout,
                'test_interval': self.pool_config.test_interval,
                'health_check_enabled': self.pool_config.health_check_enabled,
                'auto_reconnect': self.pool_config.auto_reconnect
            },
            'registered_adapters': list(self._adapters.keys()),
            'total_connections': len(self._connections),
            'active_connections': sum(1 for conn in self._connections.values() 
                                    if conn.status == ConnectionStatus.CONNECTED)
        }
    
    async def start_health_monitor(self):
        """Start the health monitoring task."""
        if self._health_monitor_task and not self._health_monitor_task.done():
            logger.warning("Health monitor already running")
            return
        
        self._is_running = True
        self._health_monitor_task = asyncio.create_task(self._health_monitor())
        logger.info("Started health monitor")
    
    async def stop_health_monitor(self):
        """Stop the health monitoring task."""
        self._is_running = False
        
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped health monitor")
    
    async def _health_monitor(self):
        """Health monitoring background task."""
        while self._is_running:
            try:
                await asyncio.sleep(self.pool_config.test_interval)
                
                if not self._is_running:
                    break
                
                # Test all active connections
                for name, connection_info in self._connections.items():
                    if connection_info.status == ConnectionStatus.CONNECTED:
                        try:
                            await self.test_connection(name)
                        except Exception as e:
                            logger.error(f"Health check failed for '{name}': {e}")
                
                # Clean up idle connections
                await self._cleanup_idle_connections()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _cleanup_idle_connections(self):
        """Clean up idle connections."""
        current_time = datetime.utcnow()
        
        for name, connection_info in self._connections.items():
            if (connection_info.status == ConnectionStatus.CONNECTED and 
                connection_info.last_used and 
                current_time - connection_info.last_used > timedelta(seconds=self.pool_config.idle_timeout)):
                
                logger.info(f"Cleaning up idle connection '{name}'")
                await self.disconnect(name)
    
    async def close_all_connections(self):
        """Close all connections."""
        for name in list(self._connections.keys()):
            await self.disconnect(name)
        
        logger.info("Closed all connections")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_health_monitor()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_health_monitor()
        await self.close_all_connections()


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """
    Get the global connection manager instance.
    
    Returns:
        ConnectionManager: Global connection manager
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


async def initialize_connection_manager(pool_config: Optional[ConnectionPoolConfig] = None) -> ConnectionManager:
    """
    Initialize the global connection manager.
    
    Args:
        pool_config: Connection pool configuration
        
    Returns:
        ConnectionManager: Initialized connection manager
    """
    global _connection_manager
    _connection_manager = ConnectionManager(pool_config)
    await _connection_manager.start_health_monitor()
    return _connection_manager


async def shutdown_connection_manager():
    """Shutdown the global connection manager."""
    global _connection_manager
    if _connection_manager:
        await _connection_manager.stop_health_monitor()
        await _connection_manager.close_all_connections()
        _connection_manager = None
