from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class QueryResult:
    answer: str
    sources: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    confidence_score: float = 0.0
    
    @property
    def has_sources(self) -> bool:
        return len(self.sources) > 0
    
    def to_dict(self) -> dict:
        return {
            'answer': self.answer,
            'sources': self.sources,
            'session_id': self.session_id,
            'confidence_score': self.confidence_score
        }