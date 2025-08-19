from typing import Optional, Tuple, List
import logging

from ...core.interfaces.service_interfaces import IAIService, ISearchService
from ...core.interfaces.repository_interfaces import ISessionRepository
from ...domain.value_objects import QueryResult


logger = logging.getLogger(__name__)


class RAGOrchestrator:
    def __init__(
        self,
        search_service: ISearchService,
        ai_service: IAIService,
        session_repository: ISessionRepository
    ):
        self.search_service = search_service
        self.ai_service = ai_service
        self.session_repo = session_repository
    
    async def process_query(
        self, 
        query: str, 
        session_id: Optional[str] = None
    ) -> QueryResult:
        try:
            if not session_id:
                session_id = await self.session_repo.create_session()
            
            search_results = await self.search_service.search(query, limit=5)
            
            context = self._build_context(search_results)
            sources = self._extract_sources(search_results)
            
            conversation_history = None
            if session_id:
                history = await self.session_repo.get_session_history(session_id)
                conversation_history = history
            
            response = await self.ai_service.generate_response(
                query=query,
                context=context,
                conversation_history=conversation_history
            )
            
            if session_id:
                await self.session_repo.save_message(session_id, "user", query)
                await self.session_repo.save_message(session_id, "assistant", response)
            
            confidence = self._calculate_confidence(search_results)
            
            return QueryResult(
                answer=response,
                sources=sources,
                session_id=session_id,
                confidence_score=confidence
            )
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return QueryResult(
                answer=f"I apologize, but I encountered an error processing your query: {str(e)}",
                sources=[],
                session_id=session_id,
                confidence_score=0.0
            )
    
    def _build_context(self, search_results: dict) -> str:
        if not search_results.get('success') or not search_results.get('results'):
            return ""
        
        context_parts = []
        for result in search_results['results'][:5]:
            source = result.get('source', 'Unknown')
            content = result.get('content', '')
            context_parts.append(f"[{source}]\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _extract_sources(self, search_results: dict) -> List[str]:
        if not search_results.get('success') or not search_results.get('results'):
            return []
        
        sources = []
        seen = set()
        
        for result in search_results['results']:
            source = result.get('source', 'Unknown')
            if source not in seen:
                sources.append(source)
                seen.add(source)
        
        return sources
    
    def _calculate_confidence(self, search_results: dict) -> float:
        if not search_results.get('success') or not search_results.get('results'):
            return 0.0
        
        results = search_results['results']
        if not results:
            return 0.0
        
        scores = [r.get('score', 1.0) for r in results[:3]]
        
        avg_score = sum(scores) / len(scores) if scores else 1.0
        
        confidence = max(0.0, min(1.0, 1.0 - avg_score))
        
        return confidence