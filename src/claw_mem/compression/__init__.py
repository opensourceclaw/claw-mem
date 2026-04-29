"""
Memory Compression Module for claw-mem v2.5.0
Includes F5 V2 compression with improved quality-to-size ratio
"""

from .memory_compression import (
    CompressionLevel,
    CompressionResult,
    KeyInformationExtractor,
    MemoryCompressor,
    get_compressor,
    compress_memory,
)

from .f5_v2 import (
    CompressionLevelV2,
    CompressionResultV2,
    F5CompressorV2,
    UltraCompressor,
    get_f5_compressor,
    get_ultra_compressor,
    compress_v2,
)

__all__ = [
    # V1
    'CompressionLevel',
    'CompressionResult',
    'KeyInformationExtractor',
    'MemoryCompressor',
    'get_compressor',
    'compress_memory',
    # V2
    'CompressionLevelV2',
    'CompressionResultV2',
    'F5CompressorV2',
    'UltraCompressor',
    'get_f5_compressor',
    'get_ultra_compressor',
    'compress_v2',
]
