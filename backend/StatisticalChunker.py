#!/usr/bin/env python3
"""
Statistical Chunker for Semantic Similarity with Overlap
Implements semantic chunking with overlap for better context preservation
"""

import numpy as np
from typing import List, Any
import logging

logger = logging.getLogger(__name__)


class Chunk:
    """Represents a text chunk with metadata"""
    def __init__(self, splits: List[str], start: int, end: int, embedding: List[float] = None):
        self.splits = splits
        self.start = start
        self.end = end
        self.embedding = embedding


class StatisticalChunker:
    """
    Statistical chunker that uses semantic similarity with overlap
    for optimal text splitting while preserving context
    """
    
    def __init__(self, encoder, min_split_tokens=100, max_split_tokens=300, overlap_tokens=50):
        self.encoder = encoder
        self.min_split_tokens = min_split_tokens
        self.max_split_tokens = max_split_tokens
        self.overlap_tokens = overlap_tokens
        
    def __call__(self, docs: List[str]) -> List[List[Chunk]]:
        """Chunk documents using statistical approach with semantic similarity"""
        chunked_docs = []
        
        for doc in docs:
            chunks = self._chunk_document(doc)
            chunked_docs.append(chunks)
        
        return chunked_docs
    
    def _chunk_document(self, doc: str) -> List[Chunk]:
        """Chunk a single document using semantic similarity with overlap"""
        # Tokenize document
        tokens = doc.split()
        
        if len(tokens) <= self.max_split_tokens:
            # Document is small enough, return as single chunk
            embedding = self.encoder([doc])[0] if self.encoder else None
            return [Chunk(splits=[doc], start=0, end=len(tokens), embedding=embedding)]
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            # Determine chunk end position
            end = min(start + self.max_split_tokens, len(tokens))
            
            # Extract chunk text
            chunk_tokens = tokens[start:end]
            chunk_text = " ".join(chunk_tokens)
            
            # Generate embedding for semantic similarity
            embedding = self.encoder([chunk_text])[0] if self.encoder else None
            
            # Create chunk
            chunk = Chunk(
                splits=[chunk_text],
                start=start,
                end=end,
                embedding=embedding
            )
            chunks.append(chunk)
            
            # Move start with overlap for context preservation
            start = end - self.overlap_tokens
            if start >= len(tokens):
                break
        
        logger.info(f"Created {len(chunks)} chunks with semantic overlap")
        return chunks
    
    def _calculate_semantic_similarity(self, chunk1: Chunk, chunk2: Chunk) -> float:
        """Calculate semantic similarity between two chunks using cosine similarity"""
        if not chunk1.embedding or not chunk2.embedding:
            return 0.0
        
        # Convert to numpy arrays
        vec1 = np.array(chunk1.embedding)
        vec2 = np.array(chunk2.embedding)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return similarity