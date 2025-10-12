# ui/streamlit_app.py
# Enhanced Streamlit UI for the Atrean RAG Platform with Database Connection Management

import streamlit as st
import requests
import json
import asyncio
from datetime import datetime
import time
import os
from typing import Dict, Any, Optional

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Import our modules for direct integration
try:
    from adapters.sqlserver_adapter import SQLServerAdapter
    from adapters.database_adapter import ConnectionConfig, DatabaseType
    from rag.nl2sql import NL2SQLGenerator
    from rag.advanced_sql_generator import AdvancedSQLGenerator
    from core.schema_introspector import SchemaIntrospector
    DIRECT_INTEGRATION = True
except ImportError:
    DIRECT_INTEGRATION = False
    st.warning("⚠️ Direct integration not available. Using API mode only.")

def test_api_connection(api_url: str) -> bool:
    """Test API connection"""
    try:
        response = requests.get(f"{api_url}/health/", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def ask_question_api(api_url: str, question: str, connection: str = "default", 
                    include_sql: bool = True, include_context: bool = True, 
                    user_id: str = None) -> dict:
    """Ask a question via the API"""
    try:
        payload = {
            "question": question,
            "connection": connection,
            "mode": "auto",
            "execute": True,
            "preview_rows": 20
        }
        if user_id:
            payload["user_id"] = user_id
            
        response = requests.post(
            f"{api_url}/nl2sql/generate",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON response: {str(e)}")

def add_connection_api(api_url: str, name: str, db_type: str, config: Dict[str, Any]) -> bool:
    """Add connection via API"""
    try:
        payload = {
            "name": name,
            "database_type": db_type,
            "config": config
        }
        response = requests.post(f"{api_url}/nl2sql/connections/add", json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to add connection: {str(e)}")
        return False

def list_connections_api(api_url: str) -> list:
    """List connections via API"""
    try:
        response = requests.get(f"{api_url}/nl2sql/connections", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return []

def initialize_session_state():
    """Initialize session state variables"""
    if 'connections' not in st.session_state:
        st.session_state.connections = {}
    if 'current_connection' not in st.session_state:
        st.session_state.current_connection = None
    if 'rag_initialized' not in st.session_state:
        st.session_state.rag_initialized = {}
    if 'nl2sql_generators' not in st.session_state:
        st.session_state.nl2sql_generators = {}

def get_puma_sample_questions() -> list:
    """Get Puma-specific sample questions"""
    return [
        "Show me all vendors and their contact information",
        "What is the total value of purchase orders by vendor?",
        "Which departments have the most purchase orders?",
        "Show me vendors with the highest order values",
        "What are the most recent purchase orders?",
        "Which vendors have pending orders?",
        "Show me the average order value by department",
        "What is the total procurement spend this year?",
        "Which vendors are most active in terms of order frequency?",
        "Show me purchase orders above $10,000"
    ]

def get_puma_advanced_questions() -> list:
    """Get Puma-specific advanced questions"""
    return [
        "Rank vendors by total order value and show their percentile rankings",
        "Show me the running total of procurement spend over time with month-over-month comparisons",
        "Calculate the standard deviation of order values by department",
        "Find vendors with above-average order values using CTEs",
        "Categorize purchase orders into value tiers (high, medium, low) using CASE statements",
        "Show me the correlation between order frequency and average order value by vendor",
        "Find vendors who haven't received orders in the last 6 months",
        "Calculate year-over-year growth in procurement spend by department",
        "Show me the top 10% of vendors by total spend using window functions",
        "Analyze seasonal patterns in procurement activity"
    ]

def get_atrean_sample_questions() -> list:
    """Get Atrean demo sample questions"""
    return [
        "What is the total revenue for all entities?",
        "Show me entities in the tech industry",
        "What is the average net income by industry?",
        "Which entities have the highest assets?",
        "How many companies are in each country?"
    ]

def get_atrean_advanced_questions() -> list:
    """Get Atrean demo advanced questions"""
    return [
        "Rank entities by revenue within each industry and show their percentile rankings",
        "Show me the running total of revenue over time with lag and lead comparisons",
        "Calculate the standard deviation and variance of revenue by industry",
        "Find entities with above-average revenue using CTEs and subqueries",
        "Categorize entities into revenue tiers (high, medium, low) using CASE statements",
        "Show me the correlation between revenue and profit margins across industries"
    ]

def display_connection_status(connection_name: str, adapter: Any) -> bool:
    """Display connection status and test connection"""
    if adapter is None:
        st.error(f"❌ Connection '{connection_name}' not available")
        return False
    
    try:
        # Test connection
        if hasattr(adapter, 'test_connection'):
            # Run async test in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                is_connected = loop.run_until_complete(adapter.test_connection())
                if is_connected:
                    st.success(f"✅ Connection '{connection_name}' is active")
                    return True
                else:
                    return False
                    return False
            finally:
                loop.close()
        else:
            st.warning(f"⚠️ Cannot test connection '{connection_name}'")
            return False
    except Exception as e:
        st.error(f"❌ Connection test error: {str(e)}")
        return False

def initialize_rag_for_connection(connection_name: str, adapter: Any) -> bool:
    """Initialize RAG system for a specific connection"""
    try:
        if connection_name in st.session_state.rag_initialized:
            st.info(f"✅ RAG already initialized for '{connection_name}'")
            return True
        
        st.info(f"🔄 Initializing RAG for '{connection_name}'...")
        
        # Determine dialect based on adapter type
        dialect = "postgresql"  # default
        if hasattr(adapter, 'database_type'):
            if adapter.database_type.value == "sqlserver":
                dialect = "sqlserver"
            elif adapter.database_type.value == "mysql":
                dialect = "mysql"
        
        # Create namespace for this connection
        namespace = f"{connection_name}_{dialect}"
        
        # Initialize NL2SQL generator
        nl2sql_gen = NL2SQLGenerator(namespace=namespace, dialect=dialect)
        
        # Build schema documents
        st.info("📚 Building schema documents...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Ensure adapter is connected before building schema documents
            if not adapter.is_connected:
                st.info("🔄 Reconnecting to database...")
                connected = loop.run_until_complete(adapter.connect())
                if not connected:
                    st.error("❌ Failed to reconnect to database")
                    return False
            
            # Build schema documents using the adapter
            loop.run_until_complete(nl2sql_gen.schema_retriever.build_schema_documents(adapter))
            
            # Store generator in session state
            st.session_state.nl2sql_generators[connection_name] = nl2sql_gen
            st.session_state.rag_initialized[connection_name] = True
            
            st.success(f"✅ RAG initialized for '{connection_name}' with schema documents")
            return True
            
        finally:
            loop.close()
            
    except Exception as e:
        st.error(f"❌ RAG initialization failed: {str(e)}")
        return False

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Atrean RAG Platform",
        page_icon="🔍",
        layout="wide"
    )
    
    initialize_session_state()
    
    st.title("🔍 Atrean RAG Platform")
    st.markdown("**Universal Database Integration with Natural Language → SQL**")
    
    # Sidebar for database connection management
    with st.sidebar:
        st.header("🗄️ Database Connection")
        
        # Database selection
        db_choice = st.selectbox(
            "Select Database", 
            ["Atrean Demo (PostgreSQL)", "Puma (SQL Server)", "Custom Connection"]
        )
        
        if db_choice == "Puma (SQL Server)":
            st.subheader("Puma SQL Server Configuration")
            
            # Puma connection form
            with st.form("puma_connection"):
                host = st.text_input("Host", value="98.70.24.81")
                port = st.number_input("Port", value=1433)
                database = st.text_input("Database", value="puma_test")
                username = st.text_input("Username", value="vineeth")
                password = st.text_input("Password", type="password", value="Fish4Lake$9")
                driver = st.text_input("ODBC Driver", value="ODBC Driver 18 for SQL Server")
                
                submitted = st.form_submit_button("1️⃣ Connect to Puma")
                
                if submitted:
                    if DIRECT_INTEGRATION:
                        try:
                            # Create connection config
                            config = ConnectionConfig(
                                host=host,
                                port=int(port),
                                database=database,
                                username=username,
                                password=password,
                                driver=driver,
                                ssl_mode=None
                            )

                            # Create adapter and CONNECT immediately
                            adapter = SQLServerAdapter(config)
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                connected = loop.run_until_complete(adapter.connect())
                            finally:
                                loop.close()

                            if connected and adapter.is_connected:
                                st.session_state.connections["puma"] = adapter
                                st.session_state.current_connection = "puma"
                                st.success("✅ Puma connection established")
                            else:
                                st.error("❌ Puma connection failed. Please verify credentials and driver.")

                        except Exception as e:
                            st.error(f"❌ Connection failed: {str(e)}")
                    else:
                        # Use API mode
                        config = {
                            "host": host,
                            "port": int(port),
                            "database": database,
                            "username": username,
                            "password": password,
                            "driver": driver,
                            "ssl_mode": None
                        }
                        
                        if add_connection_api(API_BASE_URL, "puma", "sqlserver", config):
                            st.success("✅ Puma connection added via API")
                        else:
                            st.error("❌ Failed to add Puma connection")
            
            # Test connection
            if st.button("2️⃣ Test Connection") and "puma" in st.session_state.connections:
                if DIRECT_INTEGRATION:
                    adapter = st.session_state.connections["puma"]
                    if display_connection_status("puma", adapter):
                        st.session_state.current_connection = "puma"
                else:
                    st.info("🔗 Testing connection via API...")
                    # Test via API
                    try:
                        response = requests.get(f"{API_BASE_URL}/health/", timeout=5)
                        if response.status_code == 200:
                            st.success("✅ API connection active")
                        else:
                            st.error("❌ API connection failed")
                    except Exception as e:
                        st.error(f"❌ API test failed: {str(e)}")
            
            # Initialize RAG
            if st.button("3️⃣ Initialize RAG") and "puma" in st.session_state.connections:
                if DIRECT_INTEGRATION:
                    adapter = st.session_state.connections["puma"]
                    if initialize_rag_for_connection("puma", adapter):
                        st.session_state.current_connection = "puma"
                else:
                    st.info("🔄 RAG initialization via API...")
                    # This would need API endpoint for RAG initialization
                    st.warning("⚠️ RAG initialization via API not yet implemented")
        
        elif db_choice == "Atrean Demo (PostgreSQL)":
            st.subheader("Atrean Demo Database")
            st.info("Using built-in demo data")
            
            if st.button("🔄 Initialize Demo RAG"):
                if DIRECT_INTEGRATION:
                    # Create a mock adapter for demo
                    st.session_state.connections["atrean_demo"] = "demo_adapter"
                    st.session_state.current_connection = "atrean_demo"
                    st.session_state.rag_initialized["atrean_demo"] = True
                    st.session_state.nl2sql_generators["atrean_demo"] = NL2SQLGenerator(
                        namespace="atrean_demo", 
                        dialect="postgresql"
                    )
                    st.success("✅ Demo RAG initialized")
                else:
                    st.info("🔗 Using API mode for demo")
        
        elif db_choice == "Custom Connection":
            st.subheader("Custom Database Connection")
            st.info("Custom connection configuration coming soon...")
        
        # Connection status
        st.markdown("---")
        st.subheader("📊 Connection Status")
        
        if st.session_state.current_connection:
            st.success(f"✅ Active: {st.session_state.current_connection}")
            
            if st.session_state.current_connection in st.session_state.rag_initialized:
                st.success("✅ RAG Initialized")
            else:
                st.warning("⚠️ RAG Not Initialized")
        else:
            st.info("No active connection")
        
        # Sample questions
        st.markdown("---")
        st.subheader("💡 Sample Questions")
        
        if st.session_state.current_connection == "puma":
            questions = get_puma_sample_questions()
            advanced_questions = get_puma_advanced_questions()
        else:
            questions = get_atrean_sample_questions()
            advanced_questions = get_atrean_advanced_questions()
        
        st.markdown("**Basic Questions:**")
        for i, q in enumerate(questions[:5]):
            if st.button(f"Q{i+1}: {q[:40]}...", key=f"sample_{i}"):
                st.session_state.sample_question = q
                st.rerun()
        
        st.markdown("**Advanced Questions:**")
        for i, q in enumerate(advanced_questions[:3]):
            if st.button(f"A{i+1}: {q[:40]}...", key=f"advanced_{i}"):
                st.session_state.sample_question = q
                st.rerun()
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🤖 Natural Language → SQL")
        
        # Check if sample question was selected
        if hasattr(st.session_state, 'sample_question'):
            question = st.session_state.sample_question
            del st.session_state.sample_question
        else:
            question = ""
        
        # Question input
        question = st.text_area(
            "Enter your question:",
            value=question,
            placeholder="e.g., Show me vendors with the highest order values",
            height=100
        )
        
        # Options
        col_a, col_b = st.columns(2)
        with col_a:
            include_sql = st.checkbox("Show SQL Query", value=True)
        with col_b:
            execute_query = st.checkbox("Execute Query", value=True)
        
        # Submit button
        if st.button("🚀 Generate SQL", type="primary"):
            if question.strip():
                if not st.session_state.current_connection:
                    st.error("❌ Please connect to a database first")
                elif st.session_state.current_connection not in st.session_state.rag_initialized:
                    st.error("❌ Please initialize RAG for the current connection")
                else:
                    with st.spinner("Processing your question..."):
                        try:
                            if DIRECT_INTEGRATION and st.session_state.current_connection in st.session_state.nl2sql_generators:
                                # Direct integration mode
                                nl2sql_gen = st.session_state.nl2sql_generators[st.session_state.current_connection]
                                adapter = st.session_state.connections[st.session_state.current_connection]
                                
                                # Get schema context
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                try:
                                    context = loop.run_until_complete(
                                        nl2sql_gen.schema_retriever.retrieve_schema_context(question)
                                    )
                                    
                                    # Generate SQL
                                    try:
                                        result = loop.run_until_complete(
                                            nl2sql_gen.generate_sql(question, context)
                                        )
                                    except Exception as sql_error:
                                        st.error(f"❌ Error generating SQL: {str(sql_error)}")
                                        result = None
                                    
                                    # Display results
                                    if result:
                                        st.success("✅ SQL generated successfully!")
                                        
                                        if include_sql and result.get('sql'):
                                            st.subheader("📝 Generated SQL")
                                            st.code(result['sql'], language='sql')
                                            
                                            if result.get('explanation'):
                                                with st.expander("💡 Explanation"):
                                                    st.write(result['explanation'])
                                        
                                        # Execute query if requested
                                        if execute_query and result.get('sql') and adapter != "demo_adapter":
                                            st.subheader("📊 Query Results")
                                            try:
                                                query_result = loop.run_until_complete(
                                                    adapter.execute_query(result['sql'])
                                                )
                                                
                                                if query_result.data:
                                                    st.dataframe(query_result.data)
                                                    st.info(f"📈 Returned {query_result.row_count} rows")
                                                else:
                                                    st.info("No data returned")
                                                    
                                            except Exception as e:
                                                st.error(f"❌ Query execution failed: {str(e)}")
                                        
                                        # Confidence score
                                        if result.get('confidence'):
                                            st.progress(min(max(result['confidence'], 0.0), 1.0))
                                            st.caption(f"Confidence: {result['confidence']:.2f}")
                                
                                finally:
                                    loop.close()
                            
                            else:
                                # API mode
                                response = ask_question_api(
                                    api_url=API_BASE_URL,
                                    question=question,
                                    connection=st.session_state.current_connection,
                                    include_sql=include_sql,
                                    include_context=True,
                                    user_id="streamlit_user"
                                )
                                
                                # Display results
                                st.success("✅ Question processed successfully!")
                                
                                # Answer
                                st.subheader("Answer")
                                st.write(response.get("answer", "No answer provided"))
                                
                                # SQL Query
                                if include_sql and response.get("sql"):
                                    st.subheader("SQL Query")
                                    st.code(response["sql"], language="sql")
                                    
                                    if response.get("explanation"):
                                        with st.expander("SQL Explanation"):
                                            st.write(response["explanation"])
                                
                                # Data Preview
                                if response.get("data_preview"):
                                    st.subheader("Data Preview")
                                    st.dataframe(response["data_preview"])
                                
                                # Metadata
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Confidence", f"{response.get('confidence', 0):.2f}")
                                with col2:
                                    st.metric("Execution Time", f"{response.get('execution_time_ms', 0):.1f} ms")
                                with col3:
                                    st.metric("Rows", response.get('row_count', 0))
                        
                        except Exception as e:
                            st.error(f"❌ Error processing question: {str(e)}")
            else:
                st.warning("Please enter a question.")
    
    with col2:
        st.header("📋 Connection Info")
        
        if st.session_state.current_connection:
            st.success(f"**Active Connection:** {st.session_state.current_connection}")
            
            if st.session_state.current_connection == "puma":
                st.info("**Database:** SQL Server")
                st.info("**Schema:** Puma Procurement")
                st.info("**Tables:** Vendors, Purchase Orders, Departments, etc.")
            elif st.session_state.current_connection == "atrean_demo":
                st.info("**Database:** PostgreSQL")
                st.info("**Schema:** Financial & CRM Demo")
                st.info("**Tables:** Entities, Financial Data, etc.")
            
            if st.session_state.current_connection in st.session_state.rag_initialized:
                st.success("**RAG Status:** ✅ Initialized")
            else:
                st.warning("**RAG Status:** ⚠️ Not Initialized")
        else:
            st.info("No active connection")
        
        # Quick stats
        st.markdown("---")
        st.subheader("📊 Quick Stats")
        
        if st.session_state.current_connection:
            if st.session_state.current_connection == "puma":
                st.metric("Expected Tables", "~132")
                st.metric("Expected Columns", "~1,464")
                st.metric("Business Domains", "6+")
            else:
                st.metric("Demo Tables", "5+")
                st.metric("Demo Columns", "20+")
                st.metric("Domains", "Financial, CRM")
    
    # Footer
    st.markdown("---")
    st.markdown("**Atrean RAG Platform** - Universal Database Integration with AI-Powered Analytics")

if __name__ == "__main__":
    main()