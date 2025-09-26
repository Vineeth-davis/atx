# ui/streamlit_app.py
# Simple Streamlit UI for the Atrean RAG Platform

import streamlit as st
import requests
import json
from datetime import datetime
import time

# Configuration
import os

# Get API URL from environment variable or use default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def test_api_connection(api_url: str) -> bool:
    """Test API connection"""
    try:
        response = requests.get(f"{api_url}/health/", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def ask_question(api_url: str, question: str, include_sql: bool = True, include_context: bool = True, user_id: str = None) -> dict:
    """Ask a question via the API"""
    try:
        payload = {
            "question": question,
            "include_sql": include_sql,
            "include_context": include_context
        }
        if user_id:
            payload["user_id"] = user_id
            
        response = requests.post(
            f"{api_url}/ask/",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON response: {str(e)}")

def get_query_history(api_url: str, user_id: str = None, limit: int = 10) -> list:
    """Get query history from the API"""
    try:
        params = {"limit": limit}
        if user_id:
            params["user_id"] = user_id
            
        response = requests.get(
            f"{api_url}/ask/history",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get("queries", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch query history: {str(e)}")
        return []

def initialize_rag_system(api_url: str) -> bool:
    """Initialize the RAG system"""
    try:
        response = requests.post(f"{api_url}/ask/initialize", timeout=60)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to initialize RAG system: {str(e)}")
        return False

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Atrean RAG Platform",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Atrean RAG Platform")
    st.markdown("Ask questions about your financial and CRM data using natural language.")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        api_url = st.text_input("API URL", value=API_BASE_URL)
        
        # Test API connection
        if st.button("Test Connection"):
            if test_api_connection(api_url):
                st.success("✅ API Connected")
            else:
                st.error("❌ API Connection Failed")
        
        # Initialize RAG system
        st.markdown("---")
        st.subheader("System")
        if st.button("Initialize RAG System"):
            with st.spinner("Initializing RAG system..."):
                if initialize_rag_system(api_url):
                    st.success("✅ RAG System Initialized")
                else:
                    st.error("❌ RAG System Initialization Failed")
        
        # User ID for session tracking
        user_id = st.text_input("User ID (optional)", value="streamlit_user")
        
        # Sample questions
        st.markdown("---")
        st.subheader("Sample Questions")
        sample_questions = [
            "What is the total revenue for all entities?",
            "Show me entities in the tech industry",
            "What is the average net income by industry?",
            "Which entities have the highest assets?",
            "How many companies are in each country?"
        ]
        
        for i, sample_q in enumerate(sample_questions):
            if st.button(f"Q{i+1}: {sample_q[:30]}...", key=f"sample_{i}"):
                st.session_state.sample_question = sample_q
                st.rerun()
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Ask a Question")
        
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
            placeholder="e.g., What are the total liabilities in Company X?",
            height=100
        )
        
        # Options
        col_a, col_b = st.columns(2)
        with col_a:
            include_sql = st.checkbox("Include SQL Query", value=True)
        with col_b:
            include_context = st.checkbox("Include Context", value=True)
        
        # Submit button
        if st.button("Ask Question", type="primary"):
            if question.strip():
                with st.spinner("Processing your question..."):
                    try:
                        # Make API call
                        response = ask_question(
                            api_url=api_url,
                            question=question,
                            include_sql=include_sql,
                            include_context=include_context,
                            user_id=user_id
                        )
                        
                        # Display results
                        st.success("✅ Question processed successfully!")
                        
                        # Answer
                        st.subheader("Answer")
                        st.write(response["answer"])
                        
                        # SQL Query
                        if include_sql and response.get("sql"):
                            st.subheader("SQL Query")
                            st.code(response["sql"], language="sql")
                            
                            # SQL Explanation
                            if response.get("explanation"):
                                with st.expander("SQL Explanation"):
                                    st.write(response["explanation"])
                        
                        # Context Used
                        if include_context and response.get("context_used"):
                            st.subheader("Context Used")
                            for context in response["context_used"]:
                                context_type = context.get("type", "unknown")
                                table = context.get("table", "")
                                column = context.get("column", "")
                                description = context.get("description", "")
                                score = context.get("relevance_score", 0)
                                
                                st.write(f"• **{context_type.title()}**: {table}.{column}")
                                if description:
                                    st.write(f"  - {description}")
                                st.write(f"  - Relevance: {score:.3f}")
                        
                        # Validation Results
                        if response.get("validation"):
                            validation = response["validation"]
                            if validation.get("valid"):
                                st.success("✅ SQL Query is valid")
                            else:
                                st.error("❌ SQL Query validation failed")
                                for error in validation.get("errors", []):
                                    st.error(f"  - {error}")
                                for warning in validation.get("warnings", []):
                                    st.warning(f"  - {warning}")
                        
                        # Metadata
                        st.subheader("Metadata")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Execution Time", f"{response['execution_time_ms']:.1f} ms")
                        with col2:
                            st.metric("Confidence", f"{response['confidence']:.2f}")
                        with col3:
                            st.metric("Query ID", response["query_id"][-8:])
                        with col4:
                            timestamp = datetime.fromisoformat(response["timestamp"].replace('Z', '+00:00'))
                            st.metric("Timestamp", timestamp.strftime("%H:%M:%S"))
                        
                    except Exception as e:
                        st.error(f"❌ Error processing question: {str(e)}")
            else:
                st.warning("Please enter a question.")
    
    with col2:
        st.header("Recent Queries")
        
        # Get query history
        try:
            history = get_query_history(api_url, user_id=user_id, limit=10)
            
            if history:
                for i, query in enumerate(history):
                    with st.expander(f"Query {i+1}: {query['question'][:50]}..."):
                        st.write(f"**Question:** {query['question']}")
                        st.write(f"**Answer:** {query['answer'][:200]}...")
                        
                        if query.get('sql'):
                            st.write("**SQL:**")
                            st.code(query['sql'], language='sql')
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Confidence", f"{query['confidence']:.2f}")
                        with col_b:
                            st.metric("Time", f"{query['execution_time_ms']:.1f}ms")
                        
                        if query.get('timestamp'):
                            timestamp = datetime.fromisoformat(query['timestamp'].replace('Z', '+00:00'))
                            st.caption(f"Asked at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                st.info("No recent queries found.")
                
        except Exception as e:
            st.error(f"Failed to load query history: {str(e)}")
        
        if st.button("Refresh History"):
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("**Atrean RAG Platform** - Synthetic Data Platform with RAG workflows")

if __name__ == "__main__":
    main()
