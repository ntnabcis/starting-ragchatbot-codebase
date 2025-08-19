from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkConfig:
    chunk_size: int
    chunk_overlap: int
    
    def __post_init__(self):
        if self.chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if self.chunk_overlap < 0:
            raise ValueError("Chunk overlap must be non-negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")