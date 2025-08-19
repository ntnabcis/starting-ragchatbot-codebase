from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from ..services import CourseManagementService


@dataclass
class AddCourseRequest:
    file_path: str


@dataclass
class AddCourseResponse:
    success: bool
    message: str
    courses_added: int = 0
    chunks_added: int = 0


class AddCourseUseCase:
    def __init__(self, course_management_service: CourseManagementService):
        self.course_service = course_management_service
    
    async def execute(self, request: AddCourseRequest) -> AddCourseResponse:
        try:
            path = Path(request.file_path)
            
            if not path.exists():
                return AddCourseResponse(
                    success=False,
                    message=f"Path does not exist: {request.file_path}"
                )
            
            if path.is_file():
                success, message = await self.course_service.add_course_document(path)
                return AddCourseResponse(
                    success=success,
                    message=message,
                    courses_added=1 if success else 0,
                    chunks_added=0
                )
            
            elif path.is_dir():
                courses, chunks = await self.course_service.add_course_folder(path)
                return AddCourseResponse(
                    success=True,
                    message=f"Added {courses} courses with {chunks} total chunks",
                    courses_added=courses,
                    chunks_added=chunks
                )
            
            else:
                return AddCourseResponse(
                    success=False,
                    message=f"Invalid path type: {request.file_path}"
                )
                
        except Exception as e:
            return AddCourseResponse(
                success=False,
                message=f"Error adding course: {str(e)}"
            )