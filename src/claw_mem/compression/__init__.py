"""
Memory Compression Module for claw-mem v2.4.0
"""

from .memory_compression import (
    CompressionLevel,
    CompressionResult,
    KeyInformationExtractor,
    MemoryCompressor,
    get_compressor,
    compress_memory,
)

__all__ = [
    'CompressionLevel',
    'CompressionResult',
    'KeyInformationExtractor',
    'MemoryCompressor',
    'get_compressor',
    'compress_memory',
]
