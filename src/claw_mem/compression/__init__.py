"""
Memory Compression Module for claw-mem v2.12.0

Active memory compression based on Focus and ProMem papers:
- Focus: Sawtooth pattern, autonomous triggering, Knowledge Block
- ProMem: Three-stage verification (extraction → completion → verification)

Phase 1-3 implementation (kept lightweight):
- Phase 1: Base architecture MemoryCompressorV2 + KnowledgeBlock
- Phase 2: Rule-triggered compression (count/interval thresholds)
- Phase 3: Semantic deduplication (BM25 similarity)
"""

# Retain V1 compatibility
from .memory_compression import CompressionLevel as CompressionLevelV1
from .memory_compression import CompressionResult as CompressionResultV1
from .memory_compression import KeyInformationExtractor as KeyInformationExtractorV1
from .memory_compression import MemoryCompressor as MemoryCompressorV1
from .memory_compression import compress_memory
from .memory_compression_v2 import (  # Config; Results; Components; Main class
    CompressionConfig,
    CompressionLevel,
    CompressionResult,
    CompressionTrigger,
    KeyInformationExtractor,
    KnowledgeBlock,
    KnowledgeEntry,
    MemoryCompressorV2,
    SemanticDeduplicator,
    get_compressor,
    reset_compressor,
)

# V1 compatibility alias
MemoryCompressor = MemoryCompressorV1

from .f5_v2 import (
    CompressionLevelV2,
    CompressionResultV2,
    F5CompressorV2,
    UltraCompressor,
    compress_v2,
    get_f5_compressor,
    get_ultra_compressor,
)

__all__ = [
    # V2 (recommended)
    "CompressionConfig",
    "CompressionTrigger",
    "CompressionLevel",
    "CompressionResult",
    "KnowledgeEntry",
    "KeyInformationExtractor",
    "SemanticDeduplicator",
    "KnowledgeBlock",
    "MemoryCompressorV2",
    "get_compressor",
    "reset_compressor",
    # V1 (compatibility)
    "CompressionLevelV1",
    "CompressionResultV1",
    "KeyInformationExtractorV1",
    "MemoryCompressorV1",
    "MemoryCompressor",
    "compress_memory",
    # F5 V2
    "CompressionLevelV2",
    "CompressionResultV2",
    "F5CompressorV2",
    "UltraCompressor",
    "get_f5_compressor",
    "get_ultra_compressor",
    "compress_v2",
]
