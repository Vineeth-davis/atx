# rag/embeddings.py
# Embedding generation and management

from typing import List, Optional, Dict, Any
import openai
import numpy as np
import asyncio
import logging
from functools import lru_cache
from api.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_EMBEDDING_MODEL
        self.cache = {}  # Simple in-memory cache
        self.max_batch_size = 100  # OpenAI batch limit
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Check cache first
        cached_results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = f"{text}_{self.model}"
            if cache_key in self.cache:
                cached_results.append((i, self.cache[cache_key]))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Generate embeddings for uncached texts
        new_embeddings = []
        if uncached_texts:
            try:
                # Process in batches to respect API limits
                for i in range(0, len(uncached_texts), self.max_batch_size):
                    batch = uncached_texts[i:i + self.max_batch_size]
                    response = await self._generate_batch_embeddings(batch)
                    new_embeddings.extend(response)
                
                # Cache the new embeddings
                for text, embedding in zip(uncached_texts, new_embeddings):
                    cache_key = f"{text}_{self.model}"
                    self.cache[cache_key] = embedding
                    
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                raise
        
        # Combine cached and new results in original order
        all_results = [None] * len(texts)
        
        # Add cached results
        for i, embedding in cached_results:
            all_results[i] = embedding
        
        # Add new results
        for i, embedding in zip(uncached_indices, new_embeddings):
            all_results[i] = embedding
        
        return all_results
    
    async def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from the current model"""
        # OpenAI text-embedding-3-small has 1536 dimensions
        if "text-embedding-3-small" in self.model:
            return 1536
        elif "text-embedding-3-large" in self.model:
            return 3072
        elif "text-embedding-ada-002" in self.model:
            return 1536
        else:
            return 1536  # Default fallback
    
    def clear_cache(self):
        """Clear the embedding cache"""
        self.cache.clear()
        logger.info("Embedding cache cleared")

# Global instance
embedding_service = EmbeddingService()
