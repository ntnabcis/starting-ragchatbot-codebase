from typing import List, Optional, Dict, Any
import json

from ...core.interfaces.repository_interfaces import ICourseRepository, CourseData
from .chroma_vector_store import ChromaVectorStore


class CourseRepository(ICourseRepository):
    def __init__(self, vector_store: ChromaVectorStore):
        self.vector_store = vector_store
    
    async def get_course_by_title(self, title: str) -> Optional[CourseData]:
        results = await self.vector_store.get_by_ids([title])
        
        if results.is_empty:
            return None
        
        metadata = results.metadata[0]
        return self._metadata_to_course_data(metadata)
    
    async def get_all_courses(self) -> List[CourseData]:
        results = await self.vector_store.search("", limit=1000)
        
        courses = []
        for metadata in results.metadata:
            course_data = self._metadata_to_course_data(metadata)
            if course_data:
                courses.append(course_data)
        
        return courses
    
    async def save_course(self, course: CourseData) -> bool:
        lessons_json = json.dumps([
            {
                "lesson_number": lesson.get("lesson_number"),
                "title": lesson.get("title"),
                "lesson_link": lesson.get("lesson_link")
            }
            for lesson in course.lessons
        ])
        
        metadata = {
            "title": course.title,
            "instructor": course.instructor,
            "course_link": course.course_link,
            "lessons_json": lessons_json,
            "lesson_count": len(course.lessons)
        }
        
        return await self.vector_store.add_documents(
            documents=[course.title],
            metadata=[metadata],
            ids=[course.title]
        )
    
    async def course_exists(self, title: str) -> bool:
        course = await self.get_course_by_title(title)
        return course is not None
    
    async def get_course_count(self) -> int:
        courses = await self.get_all_courses()
        return len(courses)
    
    def _metadata_to_course_data(self, metadata: Dict[str, Any]) -> Optional[CourseData]:
        if not metadata or 'title' not in metadata:
            return None
        
        lessons = []
        if 'lessons_json' in metadata:
            try:
                lessons = json.loads(metadata['lessons_json'])
            except json.JSONDecodeError:
                lessons = []
        
        return CourseData(
            title=metadata['title'],
            course_link=metadata.get('course_link'),
            instructor=metadata.get('instructor'),
            lessons=lessons
        )