# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
claw-mem - Make OpenClaw Truly Remember

OpenClaw memory system built on evolutionary principles,
fully compatible with existing OpenClaw memory formats.

v0.9.0 Features (2026-03-22):
- 10,000x faster retrieval (0.01ms)
- 1,500x faster startup (<1ms)
- 500x less memory usage (<1MB)
- Multi-level caching (L1 LRU + L2 TTL)
- Chunked index for large datasets
- Unified configuration with hot-reload
- Proactive health monitoring
- Enhanced exception recovery (100% success)
- 100% English documentation
"""

__version__ = "4.12.0"
__author__ = "Peter Cheng"

from .config import ConfigDetector, MemoryConfig
from .decay.tiered_decay import TieredDecayEngine
from .llm_provider import LLMProvider
from .merge.conflict_detector import ConflictDetector
from .merge.semantic_merger import SemanticMergeScheduler
from .factories import ComponentFactory, get_default_factory
from .context_injection import (
    ContextFormatter,
    ContextInjector,
    InjectedContext,
    format_memory_context,
    inject_memories_to_prompt,
)
from .context import (
    ConfidenceGate,
    ConfidenceLevel,
    GateResult,
    InjectorResult,
    MemoryInjector,
)
from .data_portability import (
    DataPortability,
    ExportOptions,  # noqa: F401
    ExportResult,
    ImportOptions,
    ImportResult,
)
from .errors import (
    ConfigurationError,
    DependencyError,
    FriendlyError,
    IndexNotFoundError,
    MemoryCorruptedError,
    MemoryRetrievalError,
    NetworkError,
    PermissionDeniedError,
    ValidationError,
    WorkspaceNotFoundError,
    get_error_documentation,
)
from .gating import (
    DiskStorage,
    GatingResult,
    InMemoryStorage,
    SalienceScorer,
    VersionChain,
    WriteTimeGating,
)
from .graph import (
    ConceptMediatedGraph,
    ConceptNode,
    DummyEmbedder,
    EdgeType,
    EpisodeNode,
    FactNode,
    InMemoryGraphStorage,
    KeywordExtractor,
    LLMExtractor,
    NodeType,
    ReflectionNode,
)
from .importance import ImportanceScorer
from .memory_decay import MemoryDecay
from .memory_fix_plugin import MemoryFixPlugin
from .memory import AgentAgnosticMemory, CrossAgentSync, MemoryPool, MemoryRecord
from .memory_manager import MemoryManager
from .retrieval.hybrid_router import HybridRouter, QueryType
from .retrieval.keyword import KeywordRetriever
from .retrieval.query_reconstructor import QueryReconstructor
from .retrieval.three_tier import (
    MemoryLayer,
    MemoryResult,
    SessionStartupHook,
    ThreeTierRetriever,
    search_memory,
)
from .extraction import OpenIEExtractor, Skill, SkillExtractor, SkillStore, Triplet
from .dreaming import (
    DreamingConfig,
    DreamingPipeline,
    DreamingResult,
    SignalIngestor,
    CandidateScorer,
    ScoredCandidate,
    PatternExtractor,
    REMResult,
    Promoter,
    PromotionResult,
    Signal,
)
from .graph.graph_reasoner import GraphReasoner, PathResult
from .rule_extractor import RuleExtractor
# ConstitutionStore moved to TypeScript (src/constitution.ts)
# from .constitution import ConstitutionStore, ConstitutionEntry
from .storage.episodic import EpisodicStorage
from .storage.index import InMemoryIndex, WorkingMemoryCache
from .storage.procedural import ProceduralStorage
from .storage.semantic import SemanticStorage

__all__ = [
    # "ConstitutionStore",
    # "ConstitutionEntry",
    # v4.0.0: Cross-Agent Memory
    "AgentAgnosticMemory",
    "CrossAgentSync",
    "MemoryPool",
    "MemoryRecord",
    "MemoryManager",
    "EpisodicStorage",
    "SemanticStorage",
    "ProceduralStorage",
    "InMemoryIndex",
    "WorkingMemoryCache",
    "KeywordRetriever",
    "ConfigDetector",
    "MemoryConfig",
    "ImportanceScorer",
    "MemoryFixPlugin",
    "MemoryDecay",
    "RuleExtractor",
    "ThreeTierRetriever",
    "MemoryResult",
    "MemoryLayer",
    "search_memory",
    "SessionStartupHook",
    "ContextFormatter",
    "ContextInjector",
    "InjectedContext",
    "format_memory_context",
    "inject_memories_to_prompt",
    # Error classes
    "FriendlyError",
    "IndexNotFoundError",
    "WorkspaceNotFoundError",
    "MemoryCorruptedError",
    "PermissionDeniedError",
    "ConfigurationError",
    "MemoryRetrievalError",
    "ValidationError",
    "NetworkError",
    "DependencyError",
    "get_error_documentation",
    # Gating module (v2.1.0)
    "WriteTimeGating",
    "SalienceScorer",
    "GatingResult",
    "InMemoryStorage",
    "DiskStorage",
    "VersionChain",
    # Graph module (v2.2.0)
    "ConceptMediatedGraph",
    "NodeType",
    "EpisodeNode",
    "FactNode",
    "ReflectionNode",
    "ConceptNode",
    "EdgeType",
    "InMemoryGraphStorage",
    "DummyEmbedder",
    "LLMExtractor",
    "KeywordExtractor",
    # v3.2.0: Factory for dependency injection
    "ComponentFactory",
    "get_default_factory",
    # v4.7.0: Semantic merge pipeline
    "SemanticMergeScheduler",
    "TieredDecayEngine",
    "ConflictDetector",
    "LLMProvider",
    # v4.8.0: Query reconstruction + hybrid routing
    "QueryReconstructor",
    "HybridRouter",
    "QueryType",
    # v4.9.0: Context control plane
    "MemoryInjector",
    "ConfidenceGate",
    "ConfidenceLevel",
    "GateResult",
    "InjectorResult",
    # v4.10.0: OpenIE extraction + graph reasoning
    "OpenIEExtractor",
    "Triplet",
    "GraphReasoner",
    "PathResult",
    # v4.11.0: Skill extraction
    "Skill",
    "SkillExtractor",
    "SkillStore",
    # v4.12.0: Dreaming Engine
    "DreamingConfig",
    "DreamingPipeline",
    "DreamingResult",
    "SignalIngestor",
    "CandidateScorer",
    "ScoredCandidate",
    "PatternExtractor",
    "REMResult",
    "Promoter",
    "PromotionResult",
    "Signal",
]
