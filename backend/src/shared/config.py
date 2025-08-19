import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


@dataclass
class AppConfig:
    anthropic_api_key: str
    anthropic_model: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    max_search_results: int
    max_conversation_history: int
    chroma_db_path: str
    app_name: str
    app_version: str
    debug_mode: bool
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "800")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "100")),
            max_search_results=int(os.getenv("MAX_SEARCH_RESULTS", "5")),
            max_conversation_history=int(os.getenv("MAX_CONVERSATION_HISTORY", "10")),
            chroma_db_path=os.getenv("CHROMA_DB_PATH", "./chroma_db"),
            app_name=os.getenv("APP_NAME", "Course Materials RAG System"),
            app_version=os.getenv("APP_VERSION", "2.0.0"),
            debug_mode=os.getenv("DEBUG", "false").lower() == "true"
        )
    
    def validate(self) -> None:
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        
        if self.chunk_size <= 0:
            raise ValueError("CHUNK_SIZE must be positive")
        
        if self.chunk_overlap < 0:
            raise ValueError("CHUNK_OVERLAP must be non-negative")
        
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be less than CHUNK_SIZE")