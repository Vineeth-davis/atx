# # api/config.py
# # Configuration management using Pydantic Settings

# from pydantic_settings import BaseSettings
# from typing import Optional

# class Settings(BaseSettings):
#     # Database Configuration
#     DATABASE_URL: str = "postgresql://atx:atx_pw@localhost:5432/atx_db"
    
#     # OpenAI Configuration
#     OPENAI_API_KEY: str
#     OPENAI_MODEL: str = "gpt-4o"
#     OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
#     # Vector Store Configuratio
#     VECTOR_STORE_TYPE: str = "faiss"
#     VECTOR_STORE_PATH: str = "./data/vector_store"
#     PINECONE_API_KEY: Optional[str] = None
#     PINECONE_ENVIRONMENT: Optional[str] = None
    
#     # External APIs (Optional)
#     SEC_API_KEY: Optional[str] = None
#     YAHOO_FINANCE_API_KEY: Optional[str] = None
    
#     # Application Configuration
#     APP_NAME: str = "Atrean RAG Platform"
#     APP_VERSION: str = "1.0.0"
#     DEBUG: bool = True
#     LOG_LEVEL: str = "INFO"
    
#     # Optional Streamlit UI
#     STREAMLIT_PORT: int = 8501
    
#     class Config:
#         env_file = ".env"
#         case_sensitive = True

# settings = Settings()
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = "postgresql://atx:atx_pw@postgres:5432/atx_db"
    
    # OpenAI Configuration (optional at import time; validate lazily where used)
    OPENAI_API_KEY: Optional[str] = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Vector Store Configuration
    VECTOR_STORE_TYPE: str = "faiss"
    VECTOR_STORE_PATH: str = "./data/vector_store"
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    
    # External APIs (Optional)
    SEC_API_KEY: Optional[str] = None
    YAHOO_FINANCE_API_KEY: Optional[str] = None
    PERPLEXITY_API_KEY: Optional[str] = None
    
    # Enrichment Agent Configuration
    ENABLE_ENRICHMENT: bool = True
    ENRICHMENT_CACHE_TTL: int = 3600  # 1 hour cache
    ENRICHMENT_TIMEOUT: int = 30  # 30 seconds timeout
    
    # Application Configuration
    APP_NAME: str = "Atrean RAG Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Optional Streamlit UI
    STREAMLIT_PORT: int = 8501
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()