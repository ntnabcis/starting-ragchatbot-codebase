from typing import List, Optional, Dict, Any

from ...core.interfaces.repository_interfaces import IDocumentRepository
from .chroma_vector_store import ChromaVectorStore


class DocumentRepository(IDocumentRepository):
    def __init__(self, vector_store: ChromaVectorStore):
        self.vector_store = vector_store
    
    async def save_document_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        if not chunks:
            return True
        
        documents = [chunk['content'] for chunk in chunks]
        metadata = [{
            'course_title': chunk['course_title'],
            'lesson_number': chunk.get('lesson_number'),
            'chunk_index': chunk['chunk_index']
        } for chunk in chunks]
        ids = [chunk['id'] for chunk in chunks]
        
        return await self.vector_store.add_documents(documents, metadata, ids)
    
    async def get_chunks_by_course(self, course_title: str) -> List[Dict[str, Any]]:
        filter_dict = {'course_title': course_title}
        results = await self.vector_store.search("", filter=filter_dict, limit=1000)
        
        chunks = []
        for doc, meta in zip(results.documents, results.metadata):
            chunks.append({
                'content': doc,
                'course_title': meta.get('course_title'),
                'lesson_number': meta.get('lesson_number'),
                'chunk_index': meta.get('chunk_index')
            })
        
        return chunks
    
    async def search_chunks(self, query: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        results = await self.vector_store.search(query, filter=filters, limit=10)
        
        chunks = []
        for doc, meta, score in zip(results.documents, results.metadata, results.scores):
            chunks.append({
                'content': doc,
                'course_title': meta.get('course_title'),
                'lesson_number': meta.get('lesson_number'),
                'chunk_index': meta.get('chunk_index'),
                'score': score
            })
        
        return chunks