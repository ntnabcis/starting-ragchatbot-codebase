from typing import List, Optional, Dict, Any
import logging

from ...core.interfaces.service_interfaces import ISearchService
from ...core.interfaces.repository_interfaces import IDocumentRepository, ICourseRepository
from ...domain.value_objects import SearchParams


logger = logging.getLogger(__name__)


class SearchService(ISearchService):
    def __init__(
        self, 
        document_repository: IDocumentRepository,
        course_repository: ICourseRepository
    ):
        self.document_repo = document_repository
        self.course_repo = course_repository
    
    async def search(
        self, 
        query: str, 
        course_name: Optional[str] = None,
        lesson_number: Optional[int] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        try:
            params = SearchParams(
                query=query,
                course_name=course_name,
                lesson_number=lesson_number,
                limit=limit
            )
            
            resolved_course = None
            if course_name:
                resolved_course = await self._resolve_course_name(course_name)
                if not resolved_course:
                    return {
                        'success': False,
                        'error': f"No course found matching '{course_name}'",
                        'results': []
                    }
            
            filters = self._build_filters(resolved_course, lesson_number)
            chunks = await self.document_repo.search_chunks(query, filters)
            
            formatted_results = self._format_results(chunks)
            
            return {
                'success': True,
                'results': formatted_results,
                'total': len(formatted_results),
                'query': query,
                'filters': {
                    'course': resolved_course,
                    'lesson': lesson_number
                }
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    async def get_similar_courses(self, course_name: str, limit: int = 5) -> List[str]:
        try:
            all_courses = await self.course_repo.get_all_courses()
            
            course_titles = [course.title for course in all_courses]
            
            similar = []
            search_lower = course_name.lower()
            
            for title in course_titles:
                if search_lower in title.lower():
                    similar.append(title)
                    if len(similar) >= limit:
                        break
            
            return similar
            
        except Exception as e:
            logger.error(f"Failed to find similar courses: {e}")
            return []
    
    async def _resolve_course_name(self, course_name: str) -> Optional[str]:
        similar_courses = await self.get_similar_courses(course_name, limit=1)
        return similar_courses[0] if similar_courses else None
    
    def _build_filters(
        self, 
        course_title: Optional[str], 
        lesson_number: Optional[int]
    ) -> Optional[Dict]:
        if not course_title and lesson_number is None:
            return None
        
        if course_title and lesson_number is not None:
            return {
                "$and": [
                    {"course_title": course_title},
                    {"lesson_number": lesson_number}
                ]
            }
        
        if course_title:
            return {"course_title": course_title}
        
        return {"lesson_number": lesson_number}
    
    def _format_results(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        formatted = []
        
        for chunk in chunks:
            result = {
                'content': chunk['content'],
                'course': chunk.get('course_title', 'Unknown'),
                'lesson': chunk.get('lesson_number'),
                'score': chunk.get('score', 0.0),
                'source': self._build_source_string(chunk)
            }
            formatted.append(result)
        
        return formatted
    
    def _build_source_string(self, chunk: Dict[str, Any]) -> str:
        course = chunk.get('course_title', 'Unknown')
        lesson = chunk.get('lesson_number')
        
        if lesson is not None:
            return f"{course} - Lesson {lesson}"
        return course