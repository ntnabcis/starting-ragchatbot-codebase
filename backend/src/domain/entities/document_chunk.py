from typing import Optional
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    content: str
    course_title: str
    chunk_index: int
    lesson_number: Optional[int] = None
    embedding: Optional[list] = None
    
    @property
    def id(self) -> str:
        base_id = f"{self.course_title.replace(' ', '_')}_{self.chunk_index}"
        if self.lesson_number is not None:
            base_id = f"{base_id}_lesson_{self.lesson_number}"
        return base_id
    
    @property
    def has_embedding(self) -> bool:
        return self.embedding is not None and len(self.embedding) > 0
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'content': self.content,
            'course_title': self.course_title,
            'chunk_index': self.chunk_index,
            'lesson_number': self.lesson_number,
            'has_embedding': self.has_embedding
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DocumentChunk':
        return cls(
            content=data['content'],
            course_title=data['course_title'],
            chunk_index=data['chunk_index'],
            lesson_number=data.get('lesson_number'),
            embedding=data.get('embedding')
        )
    
    def __eq__(self, other):
        if not isinstance(other, DocumentChunk):
            return False
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)