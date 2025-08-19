from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class SearchResult:
    documents: List[str]
    metadata: List[Dict[str, Any]]
    scores: List[float]
    
    @property
    def is_empty(self) -> bool:
        return len(self.documents) == 0


class IVectorStore(ABC):
    @abstractmethod
    async def add_documents(
        self, 
        documents: List[str], 
        metadata: List[Dict[str, Any]], 
        ids: List[str]
    ) -> bool:
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        filter: Optional[Dict] = None, 
        limit: int = 5
    ) -> SearchResult:
        pass
    
    @abstractmethod
    async def delete_by_ids(self, ids: List[str]) -> bool:
        pass
    
    @abstractmethod
    async def clear_collection(self) -> bool:
        pass
    
    @abstractmethod
    async def get_by_ids(self, ids: List[str]) -> SearchResult:
        pass


class IDocumentStore(ABC):
    @abstractmethod
    async def store_document(self, document_id: str, content: bytes, metadata: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    async def retrieve_document(self, document_id: str) -> Optional[bytes]:
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        pass
    
    @abstractmethod
    async def list_documents(self, filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        pass