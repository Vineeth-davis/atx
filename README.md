# Atrean RAG Platform

A synthetic data platform with RAG (Retrieval-Augmented Generation) workflows and advanced agent capabilities for financial and CRM data analysis.

## Overview

This platform enables natural language querying of multi-table relational datasets with explainable SQL generation, semantic retrieval, and multi-agent orchestration.

## Features

- **Multi-table Dataset**: ≥5 tables with financial and CRM data
- **Natural Language to SQL**: Convert questions to SQL with joins and aggregations
- **Semantic Retrieval**: Vector-based context retrieval for improved accuracy
- **Explainable Output**: Returns SQL query, answer, and context used
- **Multi-agent Architecture**: Retrieval, Analysis, Enrichment, and Policy agents
- **Query Logging**: Comprehensive logging for debugging and observability
- **Optional Streamlit UI**: Simple web interface for question answering

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (Docker recommended)
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd atrean-rag-platform
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Start PostgreSQL with Docker:
```bash
cd infra
docker-compose up -d
```

6. Load the dataset:
```bash
python scripts/load_dataset.py
```

7. Build embeddings:
```bash
python scripts/build_embeddings.py
```

8. Start the API server:
```bash
python -m api.main
```

9. (Optional) Start Streamlit UI:
```bash
streamlit run ui/streamlit_app.py
```

## API Endpoints

- `GET /health/` - Health check
- `POST /ask/` - Ask questions about the data
- `GET /schema/` - Get database schema information
- `GET /logs/` - Get query logs

## Project Structure

```
├── api/                    # FastAPI application
│   ├── routes/            # API endpoints
│   ├── config.py         # Configuration management
│   └── main.py           # Application entry point
├── db/                    # Database models and connection
│   ├── models.py         # SQLAlchemy models
│   └── connection.py     # Database connection
├── rag/                   # RAG components
│   ├── embeddings.py     # Embedding generation
│   ├── vector_store.py   # Vector database
│   ├── retriever.py      # Semantic retrieval
│   └── nl2sql.py         # Natural language to SQL
├── agents/                # Multi-agent system
│   ├── orchestrator.py   # Main orchestration
│   ├── retrieval_agent.py
│   ├── analysis_agent.py
│   ├── enrichment_agent.py
│   └── policy_agent.py
├── scripts/               # Utility scripts
│   ├── load_dataset.py   # Dataset loading
│   ├── build_embeddings.py
│   └── demo_queries.py   # Demo queries
├── ui/                    # Streamlit UI
│   └── streamlit_app.py
├── infra/                 # Infrastructure
│   ├── docker-compose.yml
│   └── init.sql
└── ai_docs/               # Documentation
    ├── masterplan.md
    └── PROJECT_TASKS.md
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
```

### Type Checking

```bash
mypy .
```

## Demo Queries

Try these example questions:

- "What are the total liabilities in Company X?"
- "What's the YoY revenue growth in 2024?"
- "Show me all companies in the technology sector"
- "What is the average transaction amount for investments?"
- "Which companies have the highest cash reserves?"

## Configuration

Key environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key for embeddings and NL→SQL
- `VECTOR_STORE_TYPE`: Vector store type (faiss, pinecone)
- `DEBUG`: Enable debug mode

## Architecture

The platform uses a multi-agent architecture:

1. **Policy Agent**: Validates question safety
2. **Retrieval Agent**: Retrieves relevant schema and data context
3. **NL→SQL Generator**: Converts natural language to SQL
4. **Analysis Agent**: Formats and validates responses
5. **Enrichment Agent**: Adds external data (optional)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Add your license here]

## Support

For questions or issues, please [create an issue](link-to-issues) or contact the development team.
