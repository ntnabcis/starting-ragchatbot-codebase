from typing import Optional
from dataclasses import dataclass

from ..services import RAGOrchestrator
from ...domain.value_objects import QueryResult


@dataclass
class QueryCourseRequest:
    query: str
    session_id: Optional[str] = None


@dataclass
class QueryCourseResponse:
    answer: str
    sources: list
    session_id: str
    confidence_score: float
    success: bool = True
    error: Optional[str] = None


class QueryCourseUseCase:
    def __init__(self, rag_orchestrator: RAGOrchestrator):
        self.orchestrator = rag_orchestrator
    
    async def execute(self, request: QueryCourseRequest) -> QueryCourseResponse:
        try:
            result = await self.orchestrator.process_query(
                query=request.query,
                session_id=request.session_id
            )
            
            return QueryCourseResponse(
                answer=result.answer,
                sources=result.sources,
                session_id=result.session_id,
                confidence_score=result.confidence_score,
                success=True
            )
            
        except Exception as e:
            return QueryCourseResponse(
                answer="",
                sources=[],
                session_id=request.session_id or "",
                confidence_score=0.0,
                success=False,
                error=str(e)
            )