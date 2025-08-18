"""
Configuration module for the Course Materials RAG System.

This module centralizes all configuration settings, including API keys,
model parameters, and processing thresholds. It uses environment variables
for sensitive data and provides sensible defaults for all other settings.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
# This allows secure storage of API keys outside version control
load_dotenv()

@dataclass
class Config:
    """
    Central configuration for the RAG system.
    
    This class consolidates all system-wide settings using a dataclass
    for clean initialization and type hints. Settings are grouped by
    functionality for better organization and maintenance.
    
    Attributes:
        ANTHROPIC_API_KEY: API key for Claude AI (loaded from environment)
        ANTHROPIC_MODEL: Specific Claude model version to use
        EMBEDDING_MODEL: HuggingFace model for generating text embeddings
        CHUNK_SIZE: Target size for document chunks (affects context window)
        CHUNK_OVERLAP: Overlap between chunks to preserve context continuity
        MAX_RESULTS: Maximum semantic search results to return
        MAX_HISTORY: Number of conversation exchanges to maintain in memory
        CHROMA_PATH: Local directory for ChromaDB vector storage
    """
    
    # Anthropic API settings
    # Critical dependency - system will not function without valid API key
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    
    # Embedding model settings
    # Using sentence-transformers for semantic similarity
    # This model balances performance and accuracy for general text
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Document processing settings
    # Chunk size affects both search quality and API token usage
    # Smaller chunks = more precise retrieval but less context
    CHUNK_SIZE: int = 800       
    # Overlap ensures important information isn't split between chunks
    CHUNK_OVERLAP: int = 100     
    # Limits search results to most relevant content
    MAX_RESULTS: int = 5         
    # Conversation memory - higher values provide more context but use more tokens
    MAX_HISTORY: int = 2         
    
    # Database paths
    # ChromaDB persistent storage location
    # Will be created automatically if it doesn't exist
    CHROMA_PATH: str = "./chroma_db"

# Global config instance used throughout the application
# Initialized once at module import for consistent settings
config = Config()


