"""
Document processing module for parsing and chunking course materials.

This module handles the extraction of structured information from course
documents, including metadata parsing, lesson identification, and intelligent
text chunking for vector storage. It's designed to work with a specific
document format but can be extended for other formats.
"""

import os
import re
from typing import List, Tuple
from models import Course, Lesson, CourseChunk


class DocumentProcessor:
    """
    Processes course documents into structured data and searchable chunks.
    
    This class handles the complete pipeline from raw text files to structured
    Course objects and searchable CourseChunk objects. It implements intelligent
    sentence-based chunking with configurable overlap to maintain context.
    
    Expected Document Format:
        Line 1: Course Title: [title]
        Line 2: Course Link: [url] (optional)
        Line 3: Course Instructor: [name] (optional)
        Remaining: Lesson markers and content
        
        Lesson Format: "Lesson N: Title" followed by content
    
    Attributes:
        chunk_size: Target size for each text chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
    """
    
    def __init__(self, chunk_size: int, chunk_overlap: int):
        """
        Initialize the document processor with chunking parameters.
        
        Args:
            chunk_size: Maximum characters per chunk (affects search granularity)
            chunk_overlap: Characters to overlap (preserves context between chunks)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def read_file(self, file_path: str) -> str:
        """
        Read text content from a file with proper encoding handling.
        
        Attempts UTF-8 encoding first, then falls back to UTF-8 with error
        ignoring for files with mixed encodings. This ensures the system
        doesn't crash on malformed documents.
        
        Args:
            file_path: Path to the text file to read
            
        Returns:
            File content as a string
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If file cannot be read due to permissions
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Fallback for files with encoding issues
            # This preserves as much content as possible
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
    


    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into sentence-based chunks with configurable overlap.
        
        This method implements intelligent chunking that:
        1. Preserves sentence boundaries (doesn't split mid-sentence)
        2. Maintains context through overlapping chunks
        3. Handles abbreviations and edge cases in sentence detection
        
        The chunking strategy optimizes for semantic coherence by keeping
        related sentences together while respecting size limits.
        
        Args:
            text: Input text to be chunked
            
        Returns:
            List of text chunks, each within size limits
            
        Algorithm:
            1. Split text into sentences using regex that handles abbreviations
            2. Build chunks by accumulating sentences up to chunk_size
            3. Create overlap by including last N characters in next chunk
            4. Ensure no information is lost between chunks
        """
        
        # Normalize whitespace for consistent processing
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Advanced sentence detection regex
        # Negative lookbehinds prevent splitting on:
        # - Abbreviations like "Dr.", "Mr.", etc.
        # - Decimal numbers like "3.14"
        sentence_endings = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\!|\?)\s+(?=[A-Z])')
        sentences = sentence_endings.split(text)
        
        # Clean sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        i = 0
        
        while i < len(sentences):
            current_chunk = []
            current_size = 0
            
            # Build chunk starting from sentence i
            for j in range(i, len(sentences)):
                sentence = sentences[j]
                
                # Calculate size with space
                space_size = 1 if current_chunk else 0
                total_addition = len(sentence) + space_size
                
                # Stop if adding this sentence exceeds size limit
                # Exception: always include at least one sentence per chunk
                if current_size + total_addition > self.chunk_size and current_chunk:
                    break
                
                current_chunk.append(sentence)
                current_size += total_addition
            
            # Add chunk if we have content
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                
                # Implement overlap strategy for context preservation
                if hasattr(self, 'chunk_overlap') and self.chunk_overlap > 0:
                    # Calculate how many sentences from the end to include in next chunk
                    overlap_size = 0
                    overlap_sentences = 0
                    
                    # Work backwards to find sentences that fit in overlap window
                    for k in range(len(current_chunk) - 1, -1, -1):
                        sentence_len = len(current_chunk[k]) + (1 if k < len(current_chunk) - 1 else 0)
                        if overlap_size + sentence_len <= self.chunk_overlap:
                            overlap_size += sentence_len
                            overlap_sentences += 1
                        else:
                            break
                    
                    # Move start position considering overlap
                    next_start = i + len(current_chunk) - overlap_sentences
                    i = max(next_start, i + 1)  # Ensure we make progress
                else:
                    # No overlap - move to next sentence after current chunk
                    i += len(current_chunk)
            else:
                # No sentences fit, move to next
                i += 1
        
        return chunks




    
    def process_course_document(self, file_path: str) -> Tuple[Course, List[CourseChunk]]:
        """
        Parse a course document into structured Course and CourseChunk objects.
        
        This method handles the complete document processing pipeline:
        1. Extract course metadata from header lines
        2. Identify and parse individual lessons
        3. Chunk lesson content for vector storage
        4. Add contextual information to chunks for better search
        
        Args:
            file_path: Path to the course document file
            
        Returns:
            Tuple containing:
            - Course object with metadata and lessons
            - List of CourseChunk objects ready for vector storage
            
        Document Format Expected:
            Line 1: Course Title: [title]
            Line 2: Course Link: [url] (optional)
            Line 3: Course Instructor: [instructor] (optional)
            Following: Lesson markers ("Lesson N: Title") and content
            
        Edge Cases Handled:
            - Missing metadata lines (uses defaults)
            - Documents without lesson structure (treats as single chunk)
            - Multiple blank lines between sections
            - Lesson links immediately after lesson titles
        """
        content = self.read_file(file_path)
        filename = os.path.basename(file_path)
        
        lines = content.strip().split('\n')
        
        # Initialize metadata with sensible defaults
        # Filename as title ensures we always have an identifier
        course_title = filename  # Fallback if no title found
        course_link = None
        instructor_name = "Unknown"
        
        # Parse course title from first line
        if len(lines) >= 1 and lines[0].strip():
            title_match = re.match(r'^Course Title:\s*(.+)$', lines[0].strip(), re.IGNORECASE)
            if title_match:
                course_title = title_match.group(1).strip()
            else:
                course_title = lines[0].strip()
        
        # Parse remaining lines for course metadata
        for i in range(1, min(len(lines), 4)):  # Check first 4 lines for metadata
            line = lines[i].strip()
            if not line:
                continue
                
            # Try to match course link
            link_match = re.match(r'^Course Link:\s*(.+)$', line, re.IGNORECASE)
            if link_match:
                course_link = link_match.group(1).strip()
                continue
                
            # Try to match instructor
            instructor_match = re.match(r'^Course Instructor:\s*(.+)$', line, re.IGNORECASE)
            if instructor_match:
                instructor_name = instructor_match.group(1).strip()
                continue
        
        # Create course object with title as ID
        course = Course(
            title=course_title,
            course_link=course_link,
            instructor=instructor_name if instructor_name != "Unknown" else None
        )
        
        # Process lessons and create chunks
        course_chunks = []
        current_lesson = None
        lesson_title = None
        lesson_link = None
        lesson_content = []
        chunk_counter = 0
        
        # Start processing from line 4 (after metadata)
        start_index = 3
        if len(lines) > 3 and not lines[3].strip():
            start_index = 4  # Skip empty line after instructor
        
        i = start_index
        while i < len(lines):
            line = lines[i]
            
            # Detect lesson boundaries using pattern matching
            # Format: "Lesson N: Title" where N is lesson number
            lesson_match = re.match(r'^Lesson\s+(\d+):\s*(.+)$', line.strip(), re.IGNORECASE)
            
            if lesson_match:
                # Process previous lesson if it exists
                if current_lesson is not None and lesson_content:
                    lesson_text = '\n'.join(lesson_content).strip()
                    if lesson_text:
                        # Add lesson to course
                        lesson = Lesson(
                            lesson_number=current_lesson,
                            title=lesson_title,
                            lesson_link=lesson_link
                        )
                        course.lessons.append(lesson)
                        
                        # Create searchable chunks from lesson content
                        chunks = self.chunk_text(lesson_text)
                        for idx, chunk in enumerate(chunks):
                            # Add contextual prefix to first chunk for better search relevance
                            # This helps the AI understand the chunk's position in the course
                            if idx == 0:
                                chunk_with_context = f"Lesson {current_lesson} content: {chunk}"
                            else:
                                chunk_with_context = chunk
                            
                            course_chunk = CourseChunk(
                                content=chunk_with_context,
                                course_title=course.title,
                                lesson_number=current_lesson,
                                chunk_index=chunk_counter
                            )
                            course_chunks.append(course_chunk)
                            chunk_counter += 1
                
                # Start new lesson
                current_lesson = int(lesson_match.group(1))
                lesson_title = lesson_match.group(2).strip()
                lesson_link = None
                
                # Check if next line is a lesson link
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    link_match = re.match(r'^Lesson Link:\s*(.+)$', next_line, re.IGNORECASE)
                    if link_match:
                        lesson_link = link_match.group(1).strip()
                        i += 1  # Skip the link line so it's not added to content
                
                lesson_content = []
            else:
                # Add line to current lesson content
                lesson_content.append(line)
                
            i += 1
        
        # Process the last lesson
        if current_lesson is not None and lesson_content:
            lesson_text = '\n'.join(lesson_content).strip()
            if lesson_text:
                lesson = Lesson(
                    lesson_number=current_lesson,
                    title=lesson_title,
                    lesson_link=lesson_link
                )
                course.lessons.append(lesson)
                
                chunks = self.chunk_text(lesson_text)
                for idx, chunk in enumerate(chunks):
                    # For any chunk of each lesson, add lesson context & course title
                  
                    chunk_with_context = f"Course {course_title} Lesson {current_lesson} content: {chunk}"
                    
                    course_chunk = CourseChunk(
                        content=chunk_with_context,
                        course_title=course.title,
                        lesson_number=current_lesson,
                        chunk_index=chunk_counter
                    )
                    course_chunks.append(course_chunk)
                    chunk_counter += 1
        
        # Fallback: Handle documents without lesson structure
        # This ensures all content is indexed even if format is unexpected
        if not course_chunks and len(lines) > 2:
            remaining_content = '\n'.join(lines[start_index:]).strip()
            if remaining_content:
                chunks = self.chunk_text(remaining_content)
                for chunk in chunks:
                    course_chunk = CourseChunk(
                        content=chunk,
                        course_title=course.title,
                        chunk_index=chunk_counter  # No lesson_number for unstructured content
                    )
                    course_chunks.append(course_chunk)
                    chunk_counter += 1
        
        return course, course_chunks
