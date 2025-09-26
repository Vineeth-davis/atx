# rag/vector_store.py
# Vector store implementation with FAISS and optional Pinecone

import faiss
import numpy as np
from typing import List, Dict, Any, Optional
import json
import os
import pickle
import logging
from pathlib import Path
from api.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store implementation with FAISS backend"""
    
    def __init__(self):
        self.index = None
        self.metadata = []
        self.dimension = 1536  # OpenAI text-embedding-3-small dimension
        self.store_path = Path(settings.VECTOR_STORE_PATH)
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.store_path / "faiss_index.bin"
        self.metadata_file = self.store_path / "metadata.pkl"
        
        # Try to load existing index
        self.load_index()
    
    def create_index(self, dimension: int = None):
        """Create a new FAISS index"""
        if dimension:
            self.dimension = dimension
        
        # Use IndexFlatIP for cosine similarity (inner product)
        # Normalize vectors for cosine similarity
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        logger.info(f"Created new FAISS index with dimension {self.dimension}")
    
    def add_vectors(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]):
        """
        Add vectors and metadata to the index
        
        Args:
            vectors: List of embedding vectors
            metadata: List of metadata dictionaries corresponding to each vector
        """
        if not vectors or not metadata:
            logger.warning("No vectors or metadata provided")
            return
        
        if len(vectors) != len(metadata):
            raise ValueError("Number of vectors must match number of metadata entries")
        
        # Create index if it doesn't exist
        if self.index is None:
            self.create_index(len(vectors[0]) if vectors else self.dimension)
        
        # Convert to numpy array and normalize for cosine similarity
        vectors_array = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(vectors_array)
        
        # Add vectors to index
        self.index.add(vectors_array)
        
        # Add metadata
        self.metadata.extend(metadata)
        
        logger.info(f"Added {len(vectors)} vectors to index. Total vectors: {self.index.ntotal}")
    
    def search(self, query_vector: List[float], k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of results with metadata and similarity scores
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("No index available or index is empty")
            return []
        
        # Convert query to numpy array and normalize
        query_array = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        scores, indices = self.index.search(query_array, min(k, self.index.ntotal))
        
        # Build results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.metadata):  # Valid index
                result = {
                    'metadata': self.metadata[idx],
                    'score': float(score),
                    'index': int(idx)
                }
                results.append(result)
        
        logger.info(f"Found {len(results)} results for query")
        return results
    
    def save_index(self):
        """Save the FAISS index to disk"""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_file))
            
            # Save metadata
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            logger.info(f"Saved index with {self.index.ntotal} vectors to {self.store_path}")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise
    
    def load_index(self):
        """Load the FAISS index from disk"""
        try:
            if self.index_file.exists() and self.metadata_file.exists():
                # Load FAISS index
                self.index = faiss.read_index(str(self.index_file))
                
                # Load metadata
                with open(self.metadata_file, 'rb') as f:
                    self.metadata = pickle.load(f)
                
                logger.info(f"Loaded index with {self.index.ntotal} vectors from {self.store_path}")
            else:
                logger.info("No existing index found, will create new one when needed")
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            # Reset to None so we can create a new one
            self.index = None
            self.metadata = []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'metadata_count': len(self.metadata),
            'index_file_exists': self.index_file.exists(),
            'metadata_file_exists': self.metadata_file.exists()
        }
    
    def clear_index(self):
        """Clear the index and metadata"""
        self.index = None
        self.metadata = []
        
        # Remove files
        if self.index_file.exists():
            self.index_file.unlink()
        if self.metadata_file.exists():
            self.metadata_file.unlink()
        
        logger.info("Cleared vector store index")

class PineconeVectorStore:
    """Alternative vector store implementation using Pinecone"""
    
    def __init__(self):
        # TODO: Implement Pinecone integration
        pass
    
    def add_vectors(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]):
        """Add vectors to Pinecone"""
        # TODO: Implement Pinecone vector addition
        pass
    
    def search(self, query_vector: List[float], k: int = 10) -> List[Dict[str, Any]]:
        """Search Pinecone for similar vectors"""
        # TODO: Implement Pinecone search
        pass

# Factory function to create appropriate vector store
def create_vector_store() -> VectorStore:
    """Create vector store based on configuration"""
    if settings.VECTOR_STORE_TYPE.lower() == "pinecone":
        return PineconeVectorStore()
    else:
        return VectorStore()
