import pytest
import os
import tempfile
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from document_processor import DocumentProcessor
from models import Course, Lesson, CourseChunk


class TestDocumentProcessorInit:
    """Test DocumentProcessor initialization"""
    
    def test_init_with_valid_parameters(self):
        """Test initialization with valid chunk_size and chunk_overlap"""
        # Arrange
        chunk_size = 800
        chunk_overlap = 100
        
        # Act
        processor = DocumentProcessor(chunk_size, chunk_overlap)
        
        # Assert
        assert processor.chunk_size == 800
        assert processor.chunk_overlap == 100
    
    def test_init_with_zero_overlap(self):
        """Test initialization with zero overlap"""
        # Arrange & Act
        processor = DocumentProcessor(500, 0)
        
        # Assert
        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 0
    
    def test_init_with_large_values(self):
        """Test initialization with large chunk_size and overlap"""
        # Arrange & Act
        processor = DocumentProcessor(10000, 2000)
        
        # Assert
        assert processor.chunk_size == 10000
        assert processor.chunk_overlap == 2000


class TestReadFile:
    """Test file reading functionality"""
    
    def test_read_file_success_utf8(self):
        """Test reading a valid UTF-8 file"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        content = "This is test content\nWith multiple lines\n"
        
        # Act & Assert
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = processor.read_file(temp_path)
            assert result == content
        finally:
            os.unlink(temp_path)
    
    def test_read_file_with_special_characters(self):
        """Test reading file with special UTF-8 characters"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        content = "Special chars: é, ñ, 中文, 🎉\n"
        
        # Act & Assert
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = processor.read_file(temp_path)
            assert result == content
        finally:
            os.unlink(temp_path)
    
    def test_read_file_empty(self):
        """Test reading an empty file"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        
        # Act & Assert
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            result = processor.read_file(temp_path)
            assert result == ""
        finally:
            os.unlink(temp_path)
    
    def test_read_file_nonexistent(self):
        """Test reading a non-existent file raises FileNotFoundError"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            processor.read_file("/nonexistent/path/file.txt")
    
    @patch('builtins.open', side_effect=[UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid'), mock_open(read_data="fallback content")().return_value])
    def test_read_file_unicode_error_fallback(self, mock_file):
        """Test fallback when UTF-8 decoding fails"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        
        # Act
        result = processor.read_file("test.txt")
        
        # Assert
        assert mock_file.call_count == 2  # Called twice: once failed, once with errors='ignore'


class TestChunkText:
    """Test text chunking functionality"""
    
    def test_chunk_text_single_sentence(self):
        """Test chunking a single sentence smaller than chunk size"""
        # Arrange
        processor = DocumentProcessor(100, 10)
        text = "This is a single sentence."
        
        # Act
        chunks = processor.chunk_text(text)
        
        # Assert
        assert len(chunks) == 1
        assert chunks[0] == "This is a single sentence."
    
    def test_chunk_text_multiple_sentences_within_limit(self):
        """Test chunking multiple sentences that fit within chunk size"""
        # Arrange
        processor = DocumentProcessor(200, 10)
        text = "First sentence. Second sentence. Third sentence."
        
        # Act
        chunks = processor.chunk_text(text)
        
        # Assert
        assert len(chunks) == 1
        assert chunks[0] == "First sentence. Second sentence. Third sentence."
    
    def test_chunk_text_with_overlap(self):
        """Test chunking with overlap between chunks"""
        # Arrange
        processor = DocumentProcessor(50, 20)
        text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence here."
        
        # Act
        chunks = processor.chunk_text(text)
        
        # Assert
        assert len(chunks) > 1
        # Check that chunks have some overlap
        for i in range(len(chunks) - 1):
            # Some content should appear in consecutive chunks due to overlap
            assert any(word in chunks[i+1] for word in chunks[i].split()[-2:] if len(word) > 2)
    
    def test_chunk_text_no_overlap(self):
        """Test chunking without overlap"""
        # Arrange
        processor = DocumentProcessor(50, 0)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        
        # Act
        chunks = processor.chunk_text(text)
        
        # Assert
        assert len(chunks) > 1
        # Verify no duplicate sentences between chunks
        all_sentences = []
        for chunk in chunks:
            sentences = [s.strip() for s in chunk.split('.') if s.strip()]
            for sentence in sentences:
                assert sentence not in all_sentences  # No sentence should repeat
                all_sentences.append(sentence)
    
    def test_chunk_text_empty_string(self):
        """Test chunking an empty string"""
        # Arrange
        processor = DocumentProcessor(100, 10)
        
        # Act
        chunks = processor.chunk_text("")
        
        # Assert
        assert chunks == []
    
    def test_chunk_text_whitespace_only(self):
        """Test chunking string with only whitespace"""
        # Arrange
        processor = DocumentProcessor(100, 10)
        text = "   \n\n\t  \r\n   "
        
        # Act
        chunks = processor.chunk_text(text)
        
        # Assert
        assert chunks == []
    
    def test_chunk_text_normalized_whitespace(self):
        """Test that multiple whitespaces are normalized"""
        # Arrange
        processor = DocumentProcessor(100, 10)
        text = "This    has     multiple     spaces.\nAnd\n\nnewlines."
        
        # Act
        chunks = processor.chunk_text(text)
        
        # Assert
        assert len(chunks) == 1
        assert chunks[0] == "This has multiple spaces. And newlines."
    
    def test_chunk_text_abbreviations_handling(self):
        """Test that abbreviations don't break sentences incorrectly"""
        # Arrange
        processor = DocumentProcessor(200, 10)
        text = "Dr. Smith works at U.S.A. Inc. He is great."
        
        # Act
        chunks = processor.chunk_text(text)
        
        # Assert
        assert len(chunks) == 1
        assert "Dr. Smith" in chunks[0]
        assert "U.S.A. Inc." in chunks[0]
    
    def test_chunk_text_exclamation_question_marks(self):
        """Test sentence splitting with exclamation and question marks"""
        # Arrange
        processor = DocumentProcessor(50, 10)
        text = "First sentence! Is this second? Third sentence."
        
        # Act
        chunks = processor.chunk_text(text)
        
        # Assert
        assert all("!" in chunk or "?" in chunk or "." in chunk for chunk in chunks)
    
    def test_chunk_text_very_long_sentence(self):
        """Test chunking a sentence longer than chunk size"""
        # Arrange
        processor = DocumentProcessor(20, 5)
        text = "This is an extremely long sentence that definitely exceeds the chunk size limit."
        
        # Act
        chunks = processor.chunk_text(text)
        
        # Assert
        assert len(chunks) == 1
        # The entire sentence should be kept together even if it exceeds chunk size
        assert chunks[0] == text


class TestProcessCourseDocument:
    """Test course document processing functionality"""
    
    def test_process_standard_course_document(self):
        """Test processing a standard course document with all metadata"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        content = """Course Title: Introduction to Python
Course Link: https://example.com/python
Course Instructor: Dr. Jane Smith

Lesson 0: Getting Started
Lesson Link: https://example.com/lesson0
This is the content for lesson 0.
It has multiple lines.

Lesson 1: Variables and Types
This is lesson 1 content.
More content here."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Act
            course, chunks = processor.process_course_document(temp_path)
            
            # Assert
            assert course.title == "Introduction to Python"
            assert course.course_link == "https://example.com/python"
            assert course.instructor == "Dr. Jane Smith"
            assert len(course.lessons) == 2
            
            assert course.lessons[0].lesson_number == 0
            assert course.lessons[0].title == "Getting Started"
            assert course.lessons[0].lesson_link == "https://example.com/lesson0"
            
            assert course.lessons[1].lesson_number == 1
            assert course.lessons[1].title == "Variables and Types"
            assert course.lessons[1].lesson_link is None
            
            assert len(chunks) > 0
            assert all(chunk.course_title == "Introduction to Python" for chunk in chunks)
            
        finally:
            os.unlink(temp_path)
    
    def test_process_document_missing_metadata(self):
        """Test processing document with missing metadata fields"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        content = """Course Title: Basic Math
Course Link: 
Course Instructor: 

Lesson 0: Addition
Content for addition lesson."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Act
            course, chunks = processor.process_course_document(temp_path)
            
            # Assert
            assert course.title == "Basic Math"
            assert course.course_link is None
            assert course.instructor is None  # Instructor defaults to None when "Unknown"
            assert len(course.lessons) == 1
            
        finally:
            os.unlink(temp_path)
    
    def test_process_document_no_lessons(self):
        """Test processing document without lesson markers"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        content = """Course Title: Quick Guide
Course Link: https://example.com
Course Instructor: John Doe

This is just general content without any lesson markers.
It should still be processed and chunked properly."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Act
            course, chunks = processor.process_course_document(temp_path)
            
            # Assert
            assert course.title == "Quick Guide"
            assert len(course.lessons) == 0
            assert len(chunks) > 0
            assert chunks[0].lesson_number is None
            
        finally:
            os.unlink(temp_path)
    
    def test_process_document_empty_file(self):
        """Test processing an empty document"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = f.name
        
        try:
            # Act
            course, chunks = processor.process_course_document(temp_path)
            
            # Assert
            assert course.title == os.path.basename(temp_path)  # Falls back to filename
            assert course.course_link is None
            assert course.instructor is None
            assert len(course.lessons) == 0
            assert len(chunks) == 0
            
        finally:
            os.unlink(temp_path)
    
    def test_process_document_malformed_lesson_numbers(self):
        """Test processing document with non-sequential lesson numbers"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        content = """Course Title: Advanced Topics
Course Instructor: Test

Lesson 5: Topic A
Content A for lesson 5

Lesson 2: Topic B
Content B for lesson 2

Lesson 10: Topic C
Content C for lesson 10"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Act
            course, chunks = processor.process_course_document(temp_path)
            
            # Assert
            assert len(course.lessons) == 3
            assert course.lessons[0].lesson_number == 5
            assert course.lessons[1].lesson_number == 2
            assert course.lessons[2].lesson_number == 10
            # Verify chunks exist and have course title in their metadata
            assert len(chunks) > 0
            assert all(chunk.course_title == "Advanced Topics" for chunk in chunks)
            
        finally:
            os.unlink(temp_path)
    
    def test_process_document_with_empty_lessons(self):
        """Test processing document with lessons that have no content"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        content = """Course Title: Test Course

Lesson 0: Empty Lesson

Lesson 1: Has Content
This lesson has content.

Lesson 2: Another Empty
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Act
            course, chunks = processor.process_course_document(temp_path)
            
            # Assert
            # Only lesson with content should be added
            assert len(course.lessons) == 1
            assert course.lessons[0].lesson_number == 1
            assert course.lessons[0].title == "Has Content"
            
        finally:
            os.unlink(temp_path)
    
    def test_process_document_chunk_context(self):
        """Test that chunks get proper context (lesson number and course title)"""
        # Arrange
        processor = DocumentProcessor(50, 10)  # Small chunks to force multiple chunks
        content = """Course Title: Context Test Course
Course Instructor: Test Instructor

Lesson 0: First Lesson
This is a long content that will be split into multiple chunks to test context preservation."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Act
            course, chunks = processor.process_course_document(temp_path)
            
            # Assert
            assert len(chunks) > 0
            # Check that chunks contain course context (from line 234 in document_processor.py)
            # The actual implementation adds "Course {course_title} Lesson {lesson_number}" prefix
            assert all("Context Test Course" in chunk.content for chunk in chunks)
            assert all("Lesson 0" in chunk.content for chunk in chunks)
            # All chunks should have lesson number 0
            assert all(chunk.lesson_number == 0 for chunk in chunks)
            # All chunks should reference the course title
            assert all(chunk.course_title == "Context Test Course" for chunk in chunks)
            
        finally:
            os.unlink(temp_path)
    
    def test_process_document_case_insensitive_markers(self):
        """Test that lesson and metadata markers are case-insensitive"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        content = """course title: Case Test
COURSE LINK: https://example.com
Course INSTRUCTOR: Test Person

LESSON 0: First
Content here

lesson 1: Second
More content"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Act
            course, chunks = processor.process_course_document(temp_path)
            
            # Assert
            assert course.title == "Case Test"
            assert course.course_link == "https://example.com"
            assert course.instructor == "Test Person"
            assert len(course.lessons) == 2
            
        finally:
            os.unlink(temp_path)
    
    def test_process_document_special_characters_in_title(self):
        """Test processing document with special characters in titles"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        content = """Course Title: Python & Data Science: A Complete Guide!
Course Instructor: O'Neill, Patrick

Lesson 0: Introduction & Setup (Part 1)
Content with special chars: é, ñ, @#$%"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Act
            course, chunks = processor.process_course_document(temp_path)
            
            # Assert
            assert course.title == "Python & Data Science: A Complete Guide!"
            assert course.instructor == "O'Neill, Patrick"
            assert course.lessons[0].title == "Introduction & Setup (Part 1)"
            
        finally:
            os.unlink(temp_path)
    
    def test_process_document_fallback_to_filename(self):
        """Test that first line is used as title when no 'Course Title:' marker"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        content = """Some content without proper headers
Just random text here.
And more content to ensure it gets chunked.
Fourth line to ensure we have more than 2 lines."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_test_course.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Act
            course, chunks = processor.process_course_document(temp_path)
            
            # Assert
            # When no "Course Title:" marker, it uses the first line as title
            assert course.title == "Some content without proper headers"
            # With >2 lines and no lessons, content is chunked (code checks len(lines) > 2)
            assert len(chunks) > 0
            
        finally:
            os.unlink(temp_path)


class TestChunkTextEdgeCases:
    """Test edge cases and boundary conditions for chunk_text method"""
    
    def test_chunk_text_exact_chunk_size(self):
        """Test when text exactly matches chunk size"""
        # Arrange
        processor = DocumentProcessor(20, 5)
        text = "Exactly twenty char."  # Exactly 20 characters
        
        # Act
        chunks = processor.chunk_text(text)
        
        # Assert
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_one_over_chunk_size(self):
        """Test when text is one character over chunk size"""
        # Arrange
        processor = DocumentProcessor(20, 5)
        text = "Twenty-one character!"  # 21 characters
        
        # Act
        chunks = processor.chunk_text(text)
        
        # Assert
        assert len(chunks) == 1  # Single sentence should stay together
    
    def test_chunk_overlap_larger_than_chunk(self):
        """Test when overlap is larger than chunk content"""
        # Arrange
        processor = DocumentProcessor(30, 50)  # Overlap larger than chunk
        text = "First. Second. Third. Fourth."
        
        # Act
        chunks = processor.chunk_text(text)
        
        # Assert
        # Should still produce valid chunks despite odd configuration
        assert len(chunks) > 0
    
    def test_chunk_text_single_very_long_word(self):
        """Test chunking with a single word longer than chunk size"""
        # Arrange
        processor = DocumentProcessor(10, 2)
        text = "Supercalifragilisticexpialidocious."
        
        # Act
        chunks = processor.chunk_text(text)
        
        # Assert
        assert len(chunks) == 1
        assert chunks[0] == text  # Word should not be broken


class TestProcessCourseDocumentIntegration:
    """Integration tests for the complete document processing flow"""
    
    def test_large_document_processing(self):
        """Test processing a large document with many lessons"""
        # Arrange
        processor = DocumentProcessor(200, 50)
        
        # Generate a large document
        content = """Course Title: Comprehensive Python Course
Course Link: https://example.com/python-complete
Course Instructor: Multiple Instructors

"""
        for i in range(20):
            content += f"""Lesson {i}: Topic {i}
Lesson Link: https://example.com/lesson{i}
This is the content for lesson {i}. It contains multiple sentences.
Each lesson has substantial content to ensure proper chunking.
We want to test how the system handles many lessons.

"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Act
            course, chunks = processor.process_course_document(temp_path)
            
            # Assert
            assert course.title == "Comprehensive Python Course"
            assert len(course.lessons) == 20
            assert len(chunks) >= 20  # At least one chunk per lesson
            
            # Verify all lessons are properly numbered
            for i, lesson in enumerate(course.lessons):
                assert lesson.lesson_number == i
                assert lesson.lesson_link == f"https://example.com/lesson{i}"
            
            # Verify chunk indices are sequential
            chunk_indices = [chunk.chunk_index for chunk in chunks]
            assert chunk_indices == list(range(len(chunks)))
            
        finally:
            os.unlink(temp_path)
    
    def test_unicode_document_processing(self):
        """Test processing document with various Unicode characters"""
        # Arrange
        processor = DocumentProcessor(800, 100)
        content = """Course Title: 国际化课程 (International Course)
Course Link: https://example.com/unicode
Course Instructor: José García & 李明

Lesson 0: Introducción 🎓
¡Hola! Welcome to the course.
This lesson contains émojis 😊 and spëcial characters.

Lesson 1: 中文内容
这是中文内容。
Mixed content here."""
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Act
            course, chunks = processor.process_course_document(temp_path)
            
            # Assert
            assert "国际化课程" in course.title
            assert course.instructor == "José García & 李明"
            assert course.lessons[0].title == "Introducción 🎓"
            assert "émojis 😊" in chunks[0].content
            
        finally:
            os.unlink(temp_path)


@pytest.fixture
def sample_processor():
    """Fixture to create a standard DocumentProcessor instance"""
    return DocumentProcessor(chunk_size=800, chunk_overlap=100)


@pytest.fixture
def temp_course_file():
    """Fixture to create a temporary course file"""
    content = """Course Title: Test Course
Course Link: https://test.com
Course Instructor: Test Instructor

Lesson 0: Introduction
Test content for introduction."""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestWithFixtures:
    """Tests using pytest fixtures for better organization"""
    
    def test_standard_processing_with_fixture(self, sample_processor, temp_course_file):
        """Test standard document processing using fixtures"""
        # Act
        course, chunks = sample_processor.process_course_document(temp_course_file)
        
        # Assert
        assert course.title == "Test Course"
        assert course.course_link == "https://test.com"
        assert course.instructor == "Test Instructor"
        assert len(course.lessons) == 1
        assert len(chunks) > 0


@pytest.mark.parametrize("chunk_size,chunk_overlap,expected_behavior", [
    (100, 0, "no_overlap"),
    (100, 50, "half_overlap"),
    (100, 100, "full_overlap"),
    (50, 10, "small_chunks"),
    (1000, 100, "large_chunks"),
])
def test_chunk_configurations(chunk_size, chunk_overlap, expected_behavior):
    """Parameterized test for different chunk configurations"""
    # Arrange
    processor = DocumentProcessor(chunk_size, chunk_overlap)
    text = "First sentence. " * 20  # Create substantial text
    
    # Act
    chunks = processor.chunk_text(text)
    
    # Assert
    assert len(chunks) > 0
    
    if expected_behavior == "no_overlap":
        # Verify no content duplication between consecutive chunks
        for i in range(len(chunks) - 1):
            # Check that the end of one chunk doesn't appear at the start of the next
            assert not chunks[i+1].startswith(chunks[i][-10:]) if len(chunks[i]) > 10 else True
    
    elif expected_behavior == "small_chunks":
        # With small chunks, we should have multiple chunks
        assert len(chunks) > 5
    
    elif expected_behavior == "large_chunks":
        # With large chunks, we should have fewer chunks (adjust for actual text)
        # 20 sentences * ~15 chars = 300 chars, so with 1000 chunk size, all fits in 1 chunk
        assert len(chunks) <= 10  # Allow more chunks for sentence boundaries


@pytest.mark.parametrize("metadata_lines,expected_title,expected_instructor", [
    (["Course Title: Valid Title", "Course Instructor: Valid Name"], "Valid Title", "Valid Name"),
    (["Invalid First Line", "Course Title: Found Later"], "Invalid First Line", None),  # Uses first line as title
    (["Course Title: Only Title"], "Only Title", None),
    (["", "Course Title: After Empty Line"], "After Empty Line", None),
    (["Random text without markers"], "Random text without markers", None),
])
def test_metadata_parsing_variations(metadata_lines, expected_title, expected_instructor):
    """Parameterized test for various metadata parsing scenarios"""
    # Arrange
    processor = DocumentProcessor(800, 100)
    content = "\n".join(metadata_lines) + "\n\nGeneral content here."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    try:
        # Act
        course, _ = processor.process_course_document(temp_path)
        
        # Assert
        if expected_title:
            assert course.title == expected_title
        else:
            assert course.title == os.path.basename(temp_path)  # Fallback to filename
        
        assert course.instructor == expected_instructor
        
    finally:
        os.unlink(temp_path)


# Test for potential missing cases and recommendations
class TestMissingCoverageRecommendations:
    """
    Tests for edge cases that might require code changes for full coverage.
    These tests document behavior that might need attention.
    """
    
    def test_extremely_long_single_line(self):
        """
        Test handling of extremely long single lines (potential memory issue).
        Note: Current implementation loads entire file into memory.
        """
        # Arrange
        processor = DocumentProcessor(100, 10)
        # Create a very long single line
        long_line = "word " * 10000  # 50,000 characters
        
        # Act
        chunks = processor.chunk_text(long_line)
        
        # Assert
        assert len(chunks) > 0
        # Note: For production, consider streaming for very large files
    
    def test_concurrent_file_access(self):
        """
        Test behavior when file is being written while reading.
        Note: Current implementation doesn't handle concurrent access.
        """
        # This would require file locking or retry mechanism
        # Currently, the behavior is undefined
        pass
    
    def test_binary_file_handling(self):
        """
        Test that binary files are handled (with errors='ignore').
        Note: Current implementation has fallback for decode errors.
        """
        # Arrange
        processor = DocumentProcessor(800, 100)
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.bin', delete=False) as f:
            f.write(b'\x00\x01\x02\x03')
            temp_path = f.name
        
        try:
            # Act
            # The implementation has a fallback with errors='ignore'
            result = processor.read_file(temp_path)
            # Binary content will be ignored/converted
            assert isinstance(result, str)
        finally:
            os.unlink(temp_path)


"""
Additional test cases that would require code modifications for full coverage:

1. **Streaming Large Files**: The current implementation loads entire files into memory.
   For very large files, a streaming approach would be more efficient.

2. **Progress Callbacks**: For long-running operations on large documents,
   progress callbacks would be useful but aren't currently supported.

3. **Custom Sentence Splitters**: The regex-based sentence splitter might not work
   well for all languages or specialized content (e.g., code, mathematical formulas).

4. **Validation of Lesson Numbers**: Currently accepts any integer for lesson numbers.
   Might want to validate they're non-negative or within a reasonable range.

5. **Duplicate Lesson Numbers**: The current implementation allows duplicate lesson
   numbers. This might or might not be intended behavior.

6. **Performance Monitoring**: No built-in performance metrics for processing time
   or memory usage, which would be useful for optimization.

7. **Partial File Recovery**: If processing fails partway through a document,
   there's no way to recover the successfully processed portions.
"""