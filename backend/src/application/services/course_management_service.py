from pathlib import Path
from typing import List, Tuple, Dict, Any
import logging

from ...core.interfaces.repository_interfaces import ICourseRepository, IDocumentRepository
from ...domain.services import DocumentProcessorService
from ...domain.value_objects import ChunkConfig


logger = logging.getLogger(__name__)


class CourseManagementService:
    def __init__(
        self,
        course_repository: ICourseRepository,
        document_repository: IDocumentRepository,
        chunk_config: ChunkConfig
    ):
        self.course_repo = course_repository
        self.document_repo = document_repository
        self.doc_processor = DocumentProcessorService(chunk_config)
    
    async def add_course_document(self, file_path: Path) -> Tuple[bool, str]:
        try:
            # Run synchronous processing in executor to avoid blocking
            import asyncio
            loop = asyncio.get_event_loop()
            course, chunks = await loop.run_in_executor(
                None,
                self.doc_processor.process_course_document,
                file_path
            )
            
            if await self.course_repo.course_exists(course.title):
                return False, f"Course '{course.title}' already exists"
            
            course_data = self._course_to_data(course)
            success = await self.course_repo.save_course(course_data)
            
            if not success:
                return False, f"Failed to save course '{course.title}'"
            
            chunks_data = [self._chunk_to_dict(chunk) for chunk in chunks]
            success = await self.document_repo.save_document_chunks(chunks_data)
            
            if not success:
                await self._rollback_course(course.title)
                return False, f"Failed to save document chunks for '{course.title}'"
            
            return True, f"Successfully added course '{course.title}' with {len(chunks)} chunks"
            
        except Exception as e:
            logger.error(f"Failed to add course document: {e}")
            return False, str(e)
    
    async def add_course_folder(
        self, 
        folder_path: Path, 
        clear_existing: bool = False
    ) -> Tuple[int, int]:
        if clear_existing:
            logger.info("Clearing existing courses...")
        
        if not folder_path.exists():
            logger.error(f"Folder {folder_path} does not exist")
            return 0, 0
        
        existing_titles = await self._get_existing_course_titles()
        total_courses = 0
        total_chunks = 0
        
        for file_path in folder_path.iterdir():
            if not file_path.is_file():
                continue
            
            if not file_path.suffix.lower() in ['.txt', '.pdf', '.docx']:
                continue
            
            try:
                # Run synchronous processing in executor to avoid blocking
                import asyncio
                loop = asyncio.get_event_loop()
                course, chunks = await loop.run_in_executor(
                    None,
                    self.doc_processor.process_course_document,
                    file_path
                )
                
                if course.title in existing_titles:
                    logger.info(f"Course '{course.title}' already exists, skipping")
                    continue
                
                course_data = self._course_to_data(course)
                await self.course_repo.save_course(course_data)
                
                chunks_data = [self._chunk_to_dict(chunk) for chunk in chunks]
                await self.document_repo.save_document_chunks(chunks_data)
                
                total_courses += 1
                total_chunks += len(chunks)
                existing_titles.add(course.title)
                
                logger.info(f"Added course '{course.title}' with {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Failed to process {file_path.name}: {e}")
        
        return total_courses, total_chunks
    
    async def get_course_analytics(self) -> Dict[str, Any]:
        try:
            courses = await self.course_repo.get_all_courses()
            course_count = len(courses)
            course_titles = [course.title for course in courses]
            
            total_lessons = sum(len(course.lessons) for course in courses)
            
            return {
                'total_courses': course_count,
                'course_titles': course_titles,
                'total_lessons': total_lessons,
                'average_lessons_per_course': total_lessons / course_count if course_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get course analytics: {e}")
            return {
                'total_courses': 0,
                'course_titles': [],
                'total_lessons': 0,
                'average_lessons_per_course': 0
            }
    
    async def _get_existing_course_titles(self) -> set:
        courses = await self.course_repo.get_all_courses()
        return {course.title for course in courses}
    
    async def _rollback_course(self, course_title: str):
        logger.warning(f"Rolling back course '{course_title}'")
    
    def _course_to_data(self, course) -> Any:
        from ...core.interfaces.repository_interfaces import CourseData
        
        return CourseData(
            title=course.title,
            course_link=course.course_link,
            instructor=course.instructor,
            lessons=[lesson.to_dict() for lesson in course.lessons]
        )
    
    def _chunk_to_dict(self, chunk) -> dict:
        return {
            'id': chunk.id,
            'content': chunk.content,
            'course_title': chunk.course_title,
            'lesson_number': chunk.lesson_number,
            'chunk_index': chunk.chunk_index
        }