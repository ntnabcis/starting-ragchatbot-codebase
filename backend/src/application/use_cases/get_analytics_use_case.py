from dataclasses import dataclass
from typing import List, Optional

from ..services import CourseManagementService


@dataclass
class GetAnalyticsResponse:
    total_courses: int
    course_titles: List[str]
    total_lessons: int
    average_lessons_per_course: float
    success: bool = True
    error: Optional[str] = None


class GetAnalyticsUseCase:
    def __init__(self, course_management_service: CourseManagementService):
        self.course_service = course_management_service
    
    async def execute(self) -> GetAnalyticsResponse:
        try:
            analytics = await self.course_service.get_course_analytics()
            
            return GetAnalyticsResponse(
                total_courses=analytics['total_courses'],
                course_titles=analytics['course_titles'],
                total_lessons=analytics.get('total_lessons', 0),
                average_lessons_per_course=analytics.get('average_lessons_per_course', 0),
                success=True
            )
            
        except Exception as e:
            return GetAnalyticsResponse(
                total_courses=0,
                course_titles=[],
                total_lessons=0,
                average_lessons_per_course=0,
                success=False,
                error=str(e)
            )