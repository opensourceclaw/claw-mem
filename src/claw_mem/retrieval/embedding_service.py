# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Embedding Service for claw-mem v2.5.0
Supports OpenAI and local embedding models
"""

import os
import time
from typing import List, Optional, Dict, Any
from functools import lru_cache
import hashlib


class EmbeddingService:
    """Embedding Service

    Features:
    - OpenAI text-embedding-3-small
    - Local sentence-transformers
    - Result caching
    - Batch processing
    """

    def __init__(
        self,
        provider: str = "auto",
        model: str = "text-embedding-3-small",
        cache_dir: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ):
        """Initialize embedding service

        Args:
            provider: "openai", "local", or "auto" (try local first, fallback to openai)
            model: Model name
            cache_dir: Directory for embedding cache
            openai_api_key: OpenAI API key (if not set in env)
        """
        self.provider = provider
        self.model = model
        self.cache_dir = cache_dir or os.path.expanduser("~/.claw_mem/embedding_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

        # Get API key
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")

        # Initialize provider
        self._embedding_fn = None
        self._init_provider()

        # Cache
        self._cache: Dict[str, List[float]] = {}

    def _init_provider(self):
        """Initialize embedding provider"""
        if self.provider == "local":
            self._init_local()
        elif self.provider == "openai":
            self._init_openai()
        else:  # auto
            # Try local first
            try:
                self._init_local()
                self.provider = "local"
            except ImportError:
                try:
                    self._init_openai()
                    self.provider = "openai"
                except Exception as e:
                    print(f"Warning: Could not initialize any embedding provider: {e}")

    def _init_local(self):
        """Initialize local embedding model"""
        from sentence_transformers import SentenceTransformer

        # Default to a small, fast model
        model_name = self.model if self.model != "text-embedding-3-small" else "all-MiniLM-L6-v2"
        self._embedding_fn = SentenceTransformer(model_name)
        print(f"Using local embedding model: {model_name}")

    def _init_openai(self):
        """Initialize OpenAI embedding client"""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key required")

        try:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=self.openai_api_key)
            print(f"Using OpenAI embedding model: {self.model}")
        except ImportError:
            raise ImportError("openai package required for OpenAI embeddings")

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()

    def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache"""
        # Check memory cache
        key = self._get_cache_key(text)
        if key in self._cache:
            return self._cache[key]

        # Check disk cache
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_file):
            try:
                import json
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    self._cache[key] = data["embedding"]
                    return data["embedding"]
            except:
                pass

        return None

    def _save_to_cache(self, text: str, embedding: List[float]):
        """Save embedding to cache"""
        key = self._get_cache_key(text)
        self._cache[key] = embedding

        # Save to disk
        try:
            import json
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            with open(cache_file, 'w') as f:
                json.dump({"text": text, "embedding": embedding}, f)
        except:
            pass

    def encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Encode texts to embeddings

        Args:
            texts: List of texts to encode
            batch_size: Batch size for processing

        Returns:
            List of embeddings
        """
        if not texts:
            return []

        # Check cache for each text
        results = []
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            cached = self._get_from_cache(text)
            if cached is not None:
                results.append(cached)
            else:
                results.append(None)  # Placeholder
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Encode uncached texts
        if uncached_texts:
            embeddings = self._encode_uncached(uncached_texts, batch_size)

            # Fill in results and cache
            for idx, text, embedding in zip(uncached_indices, uncached_texts, embeddings):
                results[idx] = embedding
                self._save_to_cache(text, embedding)

        return results

    def _encode_uncached(self, texts: List[str], batch_size: int) -> List[List[float]]:
        """Encode texts without cache"""
        if self.provider == "local" and self._embedding_fn:
            return self._embedding_fn.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=len(texts) > 100
            ).tolist()

        elif self.provider == "openai" and hasattr(self, '_openai_client'):
            # OpenAI API call
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = self._openai_client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)

                # Rate limiting
                if i + batch_size < len(texts):
                    time.sleep(0.1)

            return embeddings

        else:
            raise RuntimeError(f"No embedding provider available (provider: {self.provider})")

    def encode_single(self, text: str) -> List[float]:
        """Encode single text

        Args:
            text: Text to encode

        Returns:
            Embedding vector
        """
        return self.encode([text])[0]

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        # Common dimensions
        if self.provider == "local":
            if self._embedding_fn:
                return self._embedding_fn.get_sentence_embedding_dimension()
            return 384  # Default for MiniLM

        elif self.provider == "openai":
            # text-embedding-3-small: 1536, text-embedding-3-large: 3072
            if "large" in self.model:
                return 3072
            return 1536

        return 384


# Global instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(
    provider: str = "auto",
    model: str = "text-embedding-3-small"
) -> EmbeddingService:
    """Get global embedding service instance"""
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService(provider=provider, model=model)

    return _embedding_service
