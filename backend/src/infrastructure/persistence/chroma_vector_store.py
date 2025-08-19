import chromadb
from chromadb.config import Settings
from typing import List, Optional, Dict, Any
import logging

from ...core.interfaces.storage_interfaces import IVectorStore, SearchResult


logger = logging.getLogger(__name__)


class ChromaVectorStore(IVectorStore):
    def __init__(
        self, 
        persist_path: str, 
        collection_name: str,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.persist_path = persist_path
        self.collection_name = collection_name
        
        self.client = chromadb.PersistentClient(
            path=persist_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.embedding_function = chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        try:
            return self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
        except Exception as e:
            logger.error(f"Failed to create collection {self.collection_name}: {e}")
            raise
    
    async def add_documents(
        self, 
        documents: List[str], 
        metadata: List[Dict[str, Any]], 
        ids: List[str]
    ) -> bool:
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadata,
                ids=ids
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    async def search(
        self, 
        query: str, 
        filter: Optional[Dict] = None, 
        limit: int = 5
    ) -> SearchResult:
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=filter
            )
            
            return SearchResult(
                documents=results['documents'][0] if results['documents'] else [],
                metadata=results['metadatas'][0] if results['metadatas'] else [],
                scores=results['distances'][0] if results['distances'] else []
            )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return SearchResult(documents=[], metadata=[], scores=[])
    
    async def delete_by_ids(self, ids: List[str]) -> bool:
        try:
            self.collection.delete(ids=ids)
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False
    
    async def clear_collection(self) -> bool:
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self._get_or_create_collection()
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False
    
    async def get_by_ids(self, ids: List[str]) -> SearchResult:
        try:
            results = self.collection.get(ids=ids)
            
            return SearchResult(
                documents=results['documents'] if results else [],
                metadata=results['metadatas'] if results else [],
                scores=[0.0] * len(results['documents']) if results else []
            )
        except Exception as e:
            logger.error(f"Failed to get documents by IDs: {e}")
            return SearchResult(documents=[], metadata=[], scores=[])