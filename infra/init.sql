-- Initial database setup for Atrean RAG Platform
-- This file is executed when the PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema for the application
CREATE SCHEMA IF NOT EXISTS atrean;

-- Note: User 'atx' is created automatically by Docker environment variables
-- Privileges will be granted after user creation