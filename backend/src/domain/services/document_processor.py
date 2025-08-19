import re
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

from ..entities import Course, Lesson, DocumentChunk
from ..value_objects import ChunkConfig
from .text_chunker import TextChunkerService


@dataclass
class DocumentMetadata:
    title: str
    course_link: Optional[str] = None
    instructor: Optional[str] = None


class DocumentProcessorService:
    def __init__(self, chunk_config: ChunkConfig):
        self.chunk_config = chunk_config
        self.text_chunker = TextChunkerService(chunk_config)
    
    def process_course_document(self, file_path: Path) -> Tuple[Course, List[DocumentChunk]]:
        content = self._read_file(file_path)
        metadata = self._extract_metadata(content, file_path.name)
        course = self._create_course(metadata)
        
        lines = content.strip().split('\n')
        start_index = self._find_content_start(lines)
        
        lessons_data = self._extract_lessons(lines[start_index:])
        chunks = []
        chunk_counter = 0
        
        for lesson_data in lessons_data:
            lesson = Lesson(
                lesson_number=lesson_data['number'],
                title=lesson_data['title'],
                lesson_link=lesson_data.get('link')
            )
            course.add_lesson(lesson)
            
            lesson_chunks = self._create_lesson_chunks(
                lesson_data['content'],
                course.title,
                lesson.lesson_number,
                chunk_counter
            )
            chunks.extend(lesson_chunks)
            chunk_counter += len(lesson_chunks)
        
        if not chunks and len(lines) > start_index:
            content_text = '\n'.join(lines[start_index:]).strip()
            if content_text:
                chunks = self._create_content_chunks(
                    content_text,
                    course.title,
                    chunk_counter
                )
        
        return course, chunks
    
    def _read_file(self, file_path: Path) -> str:
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return file_path.read_text(encoding='utf-8', errors='ignore')
    
    def _extract_metadata(self, content: str, filename: str) -> DocumentMetadata:
        lines = content.strip().split('\n')
        metadata = DocumentMetadata(title=filename)
        
        for i, line in enumerate(lines[:4]):
            line = line.strip()
            if not line:
                continue
            
            if match := re.match(r'^Course Title:\s*(.+)$', line, re.IGNORECASE):
                metadata.title = match.group(1).strip()
            elif match := re.match(r'^Course Link:\s*(.+)$', line, re.IGNORECASE):
                metadata.course_link = match.group(1).strip()
            elif match := re.match(r'^Course Instructor:\s*(.+)$', line, re.IGNORECASE):
                metadata.instructor = match.group(1).strip()
        
        return metadata
    
    def _create_course(self, metadata: DocumentMetadata) -> Course:
        return Course(
            title=metadata.title,
            course_link=metadata.course_link,
            instructor=metadata.instructor
        )
    
    def _find_content_start(self, lines: List[str]) -> int:
        for i, line in enumerate(lines[:5]):
            if re.match(r'^Lesson\s+\d+:', line.strip(), re.IGNORECASE):
                return i
        return 4 if len(lines) > 4 else 0
    
    def _extract_lessons(self, lines: List[str]) -> List[dict]:
        lessons = []
        current_lesson = None
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if match := re.match(r'^Lesson\s+(\d+):\s*(.+)$', line.strip(), re.IGNORECASE):
                if current_lesson and current_lesson['content']:
                    lessons.append(current_lesson)
                
                current_lesson = {
                    'number': int(match.group(1)),
                    'title': match.group(2).strip(),
                    'content': []
                }
                
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if link_match := re.match(r'^Lesson Link:\s*(.+)$', next_line, re.IGNORECASE):
                        current_lesson['link'] = link_match.group(1).strip()
                        i += 1
            elif current_lesson:
                current_lesson['content'].append(line)
            
            i += 1
        
        if current_lesson and current_lesson['content']:
            lessons.append(current_lesson)
        
        for lesson in lessons:
            lesson['content'] = '\n'.join(lesson['content']).strip()
        
        return lessons
    
    def _create_lesson_chunks(
        self, 
        content: str, 
        course_title: str, 
        lesson_number: int, 
        start_index: int
    ) -> List[DocumentChunk]:
        if not content:
            return []
        
        text_chunks = self.text_chunker.chunk_text(content)
        chunks = []
        
        for idx, chunk_text in enumerate(text_chunks):
            contextualized_content = f"Course {course_title} Lesson {lesson_number} content: {chunk_text}"
            
            chunk = DocumentChunk(
                content=contextualized_content,
                course_title=course_title,
                lesson_number=lesson_number,
                chunk_index=start_index + idx
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_content_chunks(
        self, 
        content: str, 
        course_title: str, 
        start_index: int
    ) -> List[DocumentChunk]:
        text_chunks = self.text_chunker.chunk_text(content)
        chunks = []
        
        for idx, chunk_text in enumerate(text_chunks):
            chunk = DocumentChunk(
                content=chunk_text,
                course_title=course_title,
                chunk_index=start_index + idx
            )
            chunks.append(chunk)
        
        return chunks