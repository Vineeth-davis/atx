# ui/streamlit_app.py
# Simple Streamlit UI for the Atrean RAG Platform

import streamlit as st
import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

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
            try:
                response = requests.get(f"{api_url}/health/")
                if response.status_code == 200:
                    st.success("✅ API Connected")
                else:
                    st.error("❌ API Connection Failed")
            except Exception as e:
                st.error(f"❌ Connection Error: {str(e)}")
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Ask a Question")
        
        # Question input
        question = st.text_area(
            "Enter your question:",
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
                        # TODO: Implement API call to ask endpoint
                        response = {
                            "answer": "This is a placeholder response. API integration pending.",
                            "query": "SELECT 'placeholder' as result",
                            "context_used": ["placeholder_context"],
                            "trace_id": "placeholder-trace-id",
                            "latency_ms": 100,
                            "timestamp": datetime.now()
                        }
                        
                        # Display results
                        st.success("✅ Question processed successfully!")
                        
                        # Answer
                        st.subheader("Answer")
                        st.write(response["answer"])
                        
                        # SQL Query
                        if include_sql and response.get("query"):
                            st.subheader("SQL Query")
                            st.code(response["query"], language="sql")
                        
                        # Context Used
                        if include_context and response.get("context_used"):
                            st.subheader("Context Used")
                            for context in response["context_used"]:
                                st.write(f"• {context}")
                        
                        # Metadata
                        st.subheader("Metadata")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Latency", f"{response['latency_ms']} ms")
                        with col2:
                            st.metric("Trace ID", response["trace_id"])
                        with col3:
                            st.metric("Timestamp", response["timestamp"].strftime("%H:%M:%S"))
                        
                    except Exception as e:
                        st.error(f"❌ Error processing question: {str(e)}")
            else:
                st.warning("Please enter a question.")
    
    with col2:
        st.header("Recent Queries")
        
        # TODO: Implement recent queries display
        st.info("Recent queries will be displayed here once API integration is complete.")
        
        if st.button("Refresh"):
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("**Atrean RAG Platform** - Synthetic Data Platform with RAG workflows")

if __name__ == "__main__":
    main()
