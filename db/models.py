# db/models.py
# SQLAlchemy models for the Atrean RAG Platform

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from db.connection import Base
import uuid
from datetime import datetime

class Entity(Base):
    """Companies/funds/entities table"""
    __tablename__ = "entities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    region = Column(String(100))
    entity_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    financials_income = relationship("FinancialIncome", back_populates="entity")
    financials_balance = relationship("FinancialBalance", back_populates="entity")
    transactions = relationship("Transaction", back_populates="entity")

class FinancialIncome(Base):
    """Income statement data (time-series)"""
    __tablename__ = "financials_income"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)
    period = Column(String(20), nullable=False)  # e.g., "2024-Q1", "2024-01"
    revenue = Column(Float)
    cogs = Column(Float)
    gross_profit = Column(Float)
    opex = Column(Float)
    ebit = Column(Float)
    net_income = Column(Float)
    currency = Column(String(3), default="USD")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    entity = relationship("Entity", back_populates="financials_income")

class FinancialBalance(Base):
    """Balance sheet data (time-series)"""
    __tablename__ = "financials_balance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)
    period = Column(String(20), nullable=False)
    assets = Column(Float)
    liabilities = Column(Float)
    equity = Column(Float)
    cash = Column(Float)
    receivables = Column(Float)
    payables = Column(Float)
    currency = Column(String(3), default="USD")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    entity = relationship("Entity", back_populates="financials_balance")

class Transaction(Base):
    """Transaction events table"""
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    type = Column(String(50), nullable=False)  # e.g., "investment", "dividend", "acquisition"
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    counterparty = Column(String(255))
    memo = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    entity = relationship("Entity", back_populates="transactions")

class CRMCompany(Base):
    """CRM companies table"""
    __tablename__ = "crm_companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    stage = Column(String(50))  # e.g., "lead", "prospect", "customer"
    owner = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    tags = Column(Text)  # JSON string or comma-separated
    description = Column(Text)
    
    # Relationships
    activities = relationship("CRMActivity", back_populates="company")

class CRMActivity(Base):
    """CRM activities table"""
    __tablename__ = "crm_activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("crm_companies.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    type = Column(String(50), nullable=False)  # e.g., "call", "email", "meeting"
    actor = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("CRMCompany", back_populates="activities")

class QueryLog(Base):
    """Query logs for debugging and observability"""
    __tablename__ = "query_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String(36), nullable=False, unique=True)
    question = Column(Text, nullable=False)
    sql = Column(Text, nullable=False)
    answer_preview = Column(Text)
    latency_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    error = Column(Text)
    context_refs = Column(Text)  # JSON string of context references
