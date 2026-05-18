"""
Memory Compression Module for claw-mem v2.12.0

基于 Focus 和 ProMem 论文的主动记忆压缩:
- Focus: 锯齿模式，自主触发，Knowledge Block
- ProMem: 三阶段验证 (提取→补全→验证)

Phase 1-3 实现 (保持轻量):
- Phase 1: 基础架构 MemoryCompressorV2 + KnowledgeBlock
- Phase 2: 规则触发压缩 (数量/间隔阈值)
- Phase 3: 语义去重 (BM25 相似度)
"""

from .memory_compression_v2 import (
    # 配置
    CompressionConfig,
    CompressionTrigger,
    CompressionLevel,
    # 结果
    CompressionResult,
    KnowledgeEntry,
    # 组件
    KeyInformationExtractor,
    SemanticDeduplicator,
    KnowledgeBlock,
    # 主类
    MemoryCompressorV2,
    get_compressor,
    reset_compressor,
)

# 保留 V1 兼容
from .memory_compression import (
    CompressionLevel as CompressionLevelV1,
    CompressionResult as CompressionResultV1,
    KeyInformationExtractor as KeyInformationExtractorV1,
    MemoryCompressor as MemoryCompressorV1,
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
    # V2 (推荐)
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
    # V1 (兼容)
    "CompressionLevelV1",
    "CompressionResultV1",
    "KeyInformationExtractorV1",
    "MemoryCompressorV1",
    # F5 V2
    "CompressionLevelV2",
    "CompressionResultV2",
    "F5CompressorV2",
    "UltraCompressor",
    "get_f5_compressor",
    "get_ultra_compressor",
    "compress_v2",
]
