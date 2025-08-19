import re
from typing import List

from ..value_objects import ChunkConfig


class TextChunkerService:
    def __init__(self, config: ChunkConfig):
        self.config = config
        self._sentence_pattern = re.compile(
            r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\!|\?)\s+(?=[A-Z])'
        )
    
    def chunk_text(self, text: str) -> List[str]:
        text = self._normalize_whitespace(text)
        sentences = self._split_into_sentences(text)
        
        if not sentences:
            return []
        
        chunks = []
        i = 0
        
        while i < len(sentences):
            chunk_sentences = self._build_chunk(sentences, i)
            
            if chunk_sentences:
                chunks.append(' '.join(chunk_sentences))
                overlap_count = self._calculate_overlap(chunk_sentences)
                i += len(chunk_sentences) - overlap_count
            else:
                i += 1
        
        return chunks
    
    def _normalize_whitespace(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text.strip())
    
    def _split_into_sentences(self, text: str) -> List[str]:
        sentences = self._sentence_pattern.split(text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _build_chunk(self, sentences: List[str], start_idx: int) -> List[str]:
        chunk = []
        current_size = 0
        
        for j in range(start_idx, len(sentences)):
            sentence = sentences[j]
            space_size = 1 if chunk else 0
            total_addition = len(sentence) + space_size
            
            if current_size + total_addition > self.config.chunk_size and chunk:
                break
            
            chunk.append(sentence)
            current_size += total_addition
        
        return chunk
    
    def _calculate_overlap(self, chunk_sentences: List[str]) -> int:
        if self.config.chunk_overlap <= 0:
            return 0
        
        overlap_size = 0
        overlap_count = 0
        
        for k in range(len(chunk_sentences) - 1, -1, -1):
            sentence_len = len(chunk_sentences[k])
            if k < len(chunk_sentences) - 1:
                sentence_len += 1
            
            if overlap_size + sentence_len <= self.config.chunk_overlap:
                overlap_size += sentence_len
                overlap_count += 1
            else:
                break
        
        return overlap_count