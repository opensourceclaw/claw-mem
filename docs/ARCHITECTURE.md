# claw-mem Architecture Design

**Version**: 1.0  
**Date**: 2026-03-18  
**Status**: Draft (Pending Review)  
**Repository**: https://github.com/opensourceclaw/claw-mem

---

## 1. Architecture Overview

### 1.1 Design Principles

| Principle | Description |
|-----------|-------------|
| **Local-First** | Default fully local operation, no cloud dependency |
| **Zero LLM Pipeline** | L1/L2 operations require no LLM calls |
| **Keep It Simple** | Markdown-only storage, no external databases |
| **OpenClaw Compatible** | Fully compatible with existing memory formats |
| **Minimal Dependencies** | Pure Python + standard library where possible |

### 1.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    claw-mem Architecture                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Application Layer                   │   │
│  │  - CLI Interface                                 │   │
│  │  - OpenClaw Plugin                               │   │
│  │  - Python API                                    │   │
│  └────────────────────┬────────────────────────────┘   │
│                       │                                 │
│  ┌────────────────────▼────────────────────────────┐   │
│  │              Core Layer                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │   │
│  │  │ Memory   │  │Retrieval │  │ Learning │      │   │
│  │  │ Manager  │  │  Engine  │  │  Engine  │      │   │
│  └──────────┘  └──────────┘  └──────────┘      │   │
│  └────────────────────┬────────────────────────────┘   │
│                       │                                 │
│  ┌────────────────────▼────────────────────────────┐   │
│  │              Storage Layer (Markdown Files)      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │   │
│  │  │ MEMORY   │  │ memory/  │  │ memory/  │      │   │
│  │  │   .md    │  │YYYY-MM-DD│  │ skills/  │      │   │
│  │  │(Semantic)│  │(Episodic)│  │(Proced.) │      │   │
│  └──────────┘  └──────────┘  └──────────┘      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 1.3 Three-Layer Memory Architecture

**Design Rationale**: 3 layers balance academic depth and engineering simplicity.

| Architecture | Pros | Cons |
|-------------|------|------|
| **2-Layer (Competitors)** | Simple | No working memory, weak session context |
| **3-Layer (claw-mem)** | Balanced, deep enough, practical | Slightly more complex than 2-layer |
| **5-Layer (Papers)** | Academically complete | Over-engineered, hard to implement |

```
┌─────────────────────────────────────────────────────────┐
│              claw-mem 3-Layer Architecture               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  L1: Working Memory (工作记忆)                          │
│  └── In-Memory Session Cache                            │
│      - Current session context                          │
│      - Recently accessed memories (cached)              │
│      - Released on session end                          │
│      - Latency: <10ms                                   │
│      - Competitive advantage: 10x faster in-session     │
│                                                         │
│  L2: Short-term Memory (短期记忆)                       │
│  └── memory/YYYY-MM-DD.md (Episodic)                    │
│      - Daily conversation records                       │
│      - Auto-expire after 30 days                        │
│      - Context awareness, short-term recall             │
│      - Latency: <50ms                                   │
│                                                         │
│  L3: Long-term Memory (长期记忆)                        │
│  ├── MEMORY.md (Semantic)                               │
│  │   - Core facts, user preferences                     │
│  │   - Permanent storage                                │
│  │   - Latency: <100ms                                  │
│  │                                                      │
│  └── memory/skills/ (Procedural)                        │
│      - Skills, processes, workflows                     │
│      - Permanent storage                                │
│      - Latency: <100ms                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Key Insight**: L1 Working Memory provides significant competitive advantage:
- **10x faster** in-session queries (<10ms vs <100ms)
- **Better context injection** (maintains session state)
- **Smoother user experience** (no waiting)

---

## 2. Module Design

### 2.1 Module Breakdown

```
claw_mem/
├── __init__.py              # Package initialization
├── cli.py                   # Command-line interface
├── plugin.py                # OpenClaw plugin entry point
│
├── core/
│   ├── __init__.py
│   ├── memory_manager.py    # Core memory operations
│   ├── session.py           # Session management
│   └── config.py            # Configuration management
│
├── storage/
│   ├── __init__.py
│   ├── markdown_store.py    # Markdown file storage (CORE)
│   ├── index.py             # In-memory index for fast search
│   └── checkpoint.py        # Checkpoint system
│
├── retrieval/
│   ├── __init__.py
│   ├── base.py              # Retriever interface
│   ├── keyword.py           # Keyword search
│   ├── bm25.py              # BM25 search
│   └── hybrid.py            # Hybrid retriever
│
├── memory/
│   ├── __init__.py
│   ├── types.py             # Memory type definitions
│   ├── models.py            # Data models
│   ├── organizer.py         # Memory organization
│   └── decay.py             # Activation decay
│
├── learning/
│   ├── __init__.py
│   ├── extractor.py         # Extract memories from conversations
│   ├── validator.py         # Validate memory writes
│   └── audit.py             # Audit logging
│
└── utils/
    ├── __init__.py
    ├── validation.py        # Data validation
    └── logging.py           # Logging utilities
```

### 2.2 Core Module Responsibilities

#### Memory Manager (`core/memory_manager.py`)

**Responsibilities**:
- Coordinate all memory operations
- Route requests to storage backend
- Handle memory type classification
- Enforce pre-flight checks

**Key Methods**:
```python
class MemoryManager:
    def __init__(self, workspace: str, config: dict)
    
    def start_session(self, session_id: str) -> Session
    def end_session(self, session_id: str) -> None
    
    def store(self, content: str, memory_type: str, **kwargs) -> MemoryID
    def retrieve(self, query: str, limit: int = 10) -> List[Memory]
    def search(self, query: str, filters: dict = None) -> List[Memory]
    
    def inject_context(self, session: Session) -> str
    def pre_flight_check(self, operation: str, context: dict) -> bool
```

#### Storage Layer (`storage/`)

**Responsibilities**:
- Read/write Markdown files
- Maintain in-memory index for fast search
- Handle memory lifecycle
- Ensure data integrity

**Interface**:
```python
class MarkdownStore:
    def __init__(self, workspace: str)
    
    def write(self, memory: Memory) -> None
    def read(self, memory_id: MemoryID) -> Optional[Memory]
    def delete(self, memory_id: MemoryID) -> None
    def list_by_date(self, date: str) -> List[Memory]
    def search(self, query: str, limit: int = 10) -> List[Tuple[Memory, float]]
    
    def flush(self) -> None  # Write pending changes to disk
    def checkpoint(self) -> str  # Create checkpoint
```

#### Retrieval Engine (`retrieval/`)

**Responsibilities**:
- Implement search algorithms
- Combine multiple retrieval methods
- Rank and score results
- Maintain in-memory index

**Hybrid Retrieval Strategy**:
```python
class HybridRetriever:
    def __init__(self, store: MarkdownStore):
        self.store = store
        self.index = InMemoryIndex()  # N-gram + BM25
    
    def retrieve(self, query: str, limit: int = 10) -> List[Memory]:
        # 1. N-gram exact match (fastest)
        ngram_results = self.index.ngram_search(query, limit=limit)
        
        # 2. BM25 keyword match (fast)
        bm25_results = self.index.bm25_search(query, limit=limit)
        
        # 3. Combine and re-rank
        combined = self.fuse(ngram_results, bm25_results)
        return self.rerank(combined, query)[:limit]
```

#### Memory Organizer (`memory/organizer.py`)

**Responsibilities**:
- Auto-summarize memories into 4-layer hierarchy
- Apply activation decay
- Manage memory lifecycle
- Organize related memories

**4-Layer Hierarchy**:
```
Layer 0: Raw Memories (input)
    ↓ [Auto-summarize]
Layer 1: Daily Summaries (by date)
    ↓ [Extract key facts]
Layer 2: Topic Clusters (by theme)
    ↓ [Abstract core principles]
Layer 3: Core Principles (permanent)
```

---

## 3. Data Models

### 3.1 Memory Entry

```python
@dataclass
class Memory:
    id: MemoryID                    # Unique identifier (UUID)
    content: str                    # Memory content
    memory_type: MemoryType         # episodic/semantic/procedural
    created_at: datetime            # Creation timestamp
    updated_at: datetime            # Last update timestamp
    accessed_at: datetime           # Last access timestamp
    access_count: int               # Number of accesses
    importance_score: float         # 0.0 - 1.0
    activation_level: float         # Current activation (for decay)
    tags: List[str]                 # User-assigned tags
    metadata: dict                  # Additional metadata
    
    # Relationships
    parent_id: Optional[MemoryID]   # Parent memory (for hierarchy)
    related_ids: List[MemoryID]     # Related memories
```

### 3.2 Session

```python
@dataclass
class Session:
    id: str                         # Session ID
    user_id: Optional[str]          # User ID (if authenticated)
    started_at: datetime            # Session start time
    ended_at: Optional[datetime]    # Session end time
    injected_context: str           # Pre-injected memory context
    memory_access_log: List[Tuple[MemoryID, datetime]]
```

### 3.3 Learning Entry

```python
@dataclass
class LearningEntry:
    id: str                         # Unique identifier
    source_memory_id: MemoryID      # Original memory that triggered learning
    correction: str                 # User correction/feedback
    extracted_hint: str             # Extracted improvement direction
    created_at: datetime            # When this was learned
    applied_count: int              # How many times applied
    last_applied_at: Optional[datetime]
```

---

## 4. Storage Design (Markdown Only)

### 4.1 File Structure

```
~/.openclaw/workspace/
├── MEMORY.md                      # Semantic Memory (Core Facts)
├── memory/
│   ├── YYYY-MM-DD.md             # Episodic Memory (Daily Conversations)
│   ├── YYYY-MM-DD.md.checkpoint  # Checkpoint files
│   └── skills/                   # Procedural Memory
│       ├── deployment.md
│       ├── ocr-skill.md
│       └── ...
├── .claw-mem/
│   ├── index.json                # In-memory index (auto-generated)
│   ├── audit.log                 # Audit log
│   └── checkpoints/              # Checkpoint directory
└── TOOLS.md                      # User configuration (read by claw-mem)
```

### 4.2 MEMORY.md Format (Semantic)

```markdown
# MEMORY.md

<!-- Core Memory - Permanent Storage -->
<!-- Format: [timestamp] content <!-- tags: tag1, tag2 --> -->

[2026-03-18T10:00:00] User prefers DD/MM/YYYY date format <!-- tags: preference, date -->
[2026-03-18T10:05:00] User prefers Chinese communication <!-- tags: preference, language -->
[2026-03-18T10:10:00] Repository: https://github.com/opensourceclaw/claw-mem <!-- tags: project, repo -->
```

**Parsing Rules**:
- Lines starting with `#` are headers (ignored)
- Lines starting with `<!--` are comments (ignored)
- Memory entries: `[timestamp] content <!-- tags: ... -->`
- Tags are optional

### 4.3 memory/YYYY-MM-DD.md Format (Episodic)

```markdown
# 2026-03-18

## Session: session_001

[10:00] User asked about Shanghai weather
[10:05] User corrected file location preference
[10:10] Discussed claw-mem architecture

## Session: session_002

[14:00] User requested feature X
[14:15] Implemented feature X
[14:20] User approved implementation
```

**Parsing Rules**:
- `# YYYY-MM-DD` is the date header
- `## Session: <id>` marks session boundaries
- `[HH:MM] content` are memory entries
- Auto-expire after 30 days (configurable)

### 4.4 memory/skills/*.md Format (Procedural)

```markdown
# Deployment Process

1. Run tests: `pytest`
2. Build: `python -m build`
3. Publish: `twine upload dist/*`
4. Create release on GitHub
```

**Parsing Rules**:
- Standard Markdown format
- First line is the title
- Content is free-form Markdown
- Permanent storage (no expiry)

### 4.5 In-Memory Index

```python
class InMemoryIndex:
    """In-memory index for fast search, rebuilt on startup"""
    
    def __init__(self):
        self.memories: Dict[MemoryID, Memory] = {}
        self.ngram_index: Dict[str, Set[MemoryID]] = defaultdict(set)
        self.bm25_index: Optional[BM25Okapi] = None
        self.documents: List[List[str]] = []
    
    def build(self, memories: List[Memory]) -> None:
        """Build index from memories (called on startup)"""
        self.memories = {m.id: m for m in memories}
        
        # Build N-gram index
        for memory in memories:
            self._add_to_ngram(memory)
        
        # Build BM25 index
        self.documents = [self._tokenize(m.content) for m in memories]
        self.bm25_index = BM25Okapi(self.documents)
    
    def ngram_search(self, query: str, limit: int = 10) -> List[MemoryID]:
        """O(1) exact phrase matching"""
        tokens = self._tokenize(query)
        if len(tokens) < 3:
            return []
        
        ngram = ' '.join(tokens[:3])
        ids = self.ngram_index.get(ngram, set())
        return list(ids)[:limit]
    
    def bm25_search(self, query: str, limit: int = 10) -> List[Tuple[MemoryID, float]]:
        """Keyword-based relevance scoring"""
        scores = self.bm25_index.get_scores(self._tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(list(self.memories.keys())[i], score) for i, score in ranked[:limit]]
    
    def _add_to_ngram(self, memory: Memory) -> None:
        """Add memory to N-gram index"""
        tokens = self._tokenize(memory.content)
        for i in range(len(tokens) - 3 + 1):
            ngram = ' '.join(tokens[i:i+3])
            self.ngram_index[ngram].add(memory.id)
```

---

## 5. Retrieval Design

### 5.1 N-gram Index

**Purpose**: O(1) exact phrase matching

**Implementation**:
```python
class NGramIndex:
    def __init__(self, n: int = 3):
        self.n = n
        self.index: Dict[str, Set[MemoryID]] = defaultdict(set)
    
    def build(self, memory: Memory) -> None:
        tokens = self.tokenize(memory.content)
        for i in range(len(tokens) - self.n + 1):
            ngram = ' '.join(tokens[i:i+self.n])
            self.index[ngram].add(memory.id)
    
    def search(self, query: str, limit: int = 10) -> List[MemoryID]:
        tokens = self.tokenize(query)
        if len(tokens) < self.n:
            return []
        
        ngram = ' '.join(tokens[:self.n])
        return list(self.index.get(ngram, set()))[:limit]
```

### 5.2 BM25 Index

**Purpose**: Keyword-based relevance scoring

**Implementation**:
```python
from rank_bm25 import BM25Okapi

class BM25Retriever:
    def __init__(self):
        self.bm25: Optional[BM25Okapi] = None
        self.memory_ids: List[MemoryID] = []
        self.documents: List[List[str]] = []
    
    def build_index(self, memories: List[Memory]) -> None:
        self.memory_ids = [m.id for m in memories]
        self.documents = [self.tokenize(m.content) for m in memories]
        self.bm25 = BM25Okapi(self.documents)
    
    def search(self, query: str, limit: int = 10) -> List[Tuple[MemoryID, float]]:
        scores = self.bm25.get_scores(self.tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(self.memory_ids[i], score) for i, score in ranked[:limit]]
```

### 5.3 Hybrid Fusion

**Purpose**: Combine multiple retrieval methods

**Fusion Algorithm**:
```python
def reciprocal_rank_fusion(results: List[List[Tuple[MemoryID, float]]], k: int = 60):
    """
    Reciprocal Rank Fusion for combining multiple retrieval results
    """
    fused_scores: Dict[MemoryID, float] = defaultdict(float)
    
    for result_list in results:
        for rank, (memory_id, score) in enumerate(result_list):
            fused_scores[memory_id] += 1.0 / (k + rank)
    
    # Normalize and return
    sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results
```

---

## 6. Activation Decay Design

### 6.1 Ebbinghaus Forgetting Curve

**Formula**:
```
A(t) = A₀ * exp(-t/τ)

Where:
- A(t): Activation at time t
- A₀: Initial activation
- t: Time since last access
- τ: Decay constant (based on memory type)
```

**Decay Constants by Memory Type**:
| Memory Type | τ (days) | Description |
|-------------|----------|-------------|
| Episodic | 7 | Fast decay, expires in 30 days |
| Semantic | 90 | Slow decay, permanent unless deleted |
| Procedural | 180 | Very slow decay, permanent |

### 6.2 Activation Update

```python
class ActivationDecay:
    def __init__(self, decay_constants: dict):
        self.tau = decay_constants  # {'episodic': 7, 'semantic': 90, 'procedural': 180}
    
    def decay(self, memory: Memory, current_time: datetime) -> float:
        """Calculate current activation level"""
        time_diff = (current_time - memory.accessed_at).days
        initial_activation = memory.activation_level
        tau = self.tau[memory.memory_type]
        
        # Ebbinghaus formula
        current_activation = initial_activation * math.exp(-time_diff / tau)
        
        # Boost on access
        if time_diff == 0:  # Accessed today
            current_activation = min(1.0, current_activation + 0.1)
        
        return current_activation
    
    def should_expire(self, memory: Memory, threshold: float = 0.1) -> bool:
        """Check if memory should be expired"""
        if memory.memory_type == 'episodic':
            return memory.activation_level < threshold
        return False  # Semantic and procedural don't expire
```

---

## 7. Pre-flight Check Design

### 7.1 Check Registry

```python
class PreFlightCheckRegistry:
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
    
    def register(self, operation: str, check_func: Callable) -> None:
        self.checks[operation] = check_func
    
    def check(self, operation: str, context: dict) -> Tuple[bool, str]:
        """
        Returns: (passed, message)
        """
        if operation not in self.checks:
            return True, "No checks registered"
        
        try:
            result = self.checks[operation](context)
            return result.passed, result.message
        except Exception as e:
            return False, f"Check failed: {str(e)}"
```

### 7.2 Built-in Checks

```python
# File operation check
def check_file_operation(context: dict) -> CheckResult:
    """Check TOOLS.md for directory 分工 before file operations"""
    target_path = context.get('target_path')
    file_type = context.get('file_type')
    
    if not target_path:
        return CheckResult(False, "Target path not specified")
    
    # Load TOOLS.md workspace config
    workspace_config = load_tools_md_workspace_config()
    
    # Determine correct directory
    if file_type == 'daily_project':
        expected_dir = workspace_config['daily_workspace']
    elif file_type == 'system_config':
        expected_dir = workspace_config['system_config']
    else:
        return CheckResult(True, "Unknown file type, skipping check")
    
    # Validate
    if not target_path.startswith(expected_dir):
        return CheckResult(
            False,
            f"File should be in {expected_dir}, not {target_path}"
        )
    
    return CheckResult(True, "Directory check passed")

# External action check
def check_external_action(context: dict) -> CheckResult:
    """Check if external action is authorized"""
    action_type = context.get('action_type')
    authorization = context.get('authorization')
    
    if not authorization:
        return CheckResult(False, "External action requires explicit authorization")
    
    return CheckResult(True, "Authorization verified")
```

---

## 8. Security Design

### 8.1 Write Validation

```python
class MemoryWriteValidator:
    """Validate memory writes to prevent malicious injection"""
    
    FORBIDDEN_PATTERNS = [
        r'ignore\s+previous\s+instructions',
        r'output\s+hello\s+world',
        r'system\s+prompt',
        r'bypass\s+security',
        # Add more patterns as needed
    ]
    
    def validate(self, content: str) -> ValidationResult:
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return ValidationResult(
                    valid=False,
                    reason=f"Content matches forbidden pattern: {pattern}"
                )
        
        # Additional validation
        if len(content) > MAX_MEMORY_SIZE:
            return ValidationResult(
                valid=False,
                reason=f"Content exceeds maximum size ({MAX_MEMORY_SIZE})"
            )
        
        return ValidationResult(valid=True)
```

### 8.2 Audit Logging

```python
class AuditLogger:
    def __init__(self, log_path: str):
        self.log_path = log_path
    
    def log(self, action: str, memory_id: str, old_value: str = None, 
            new_value: str = None, performed_by: str = "system") -> None:
        """Log memory modification to audit.log"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {action} memory={memory_id} by={performed_by}\n"
        
        with open(self.log_path, 'a') as f:
            f.write(log_entry)
    
    def get_history(self, memory_id: str) -> List[str]:
        """Get modification history for a memory"""
        history = []
        with open(self.log_path, 'r') as f:
            for line in f:
                if f'memory={memory_id}' in line:
                    history.append(line.strip())
        return history
```

---

## 9. API Design

### 9.1 Python API

```python
from claw_mem import MemoryManager, MemoryType, Session

# Initialize
memory = MemoryManager(
    workspace="/Users/you/.openclaw/workspace",
    config={
        'decay_constants': {'episodic': 7, 'semantic': 90, 'procedural': 180},
        'retrieval_weights': {'ngram': 0.7, 'bm25': 0.3},
        'enable_audit': True,
    }
)

# Start session
session = memory.start_session("session_001")

# Store memory
memory_id = memory.store(
    content="User prefers DD/MM/YYYY date format",
    memory_type=MemoryType.SEMANTIC,
    tags=['preference', 'date']
)

# Retrieve memory
results = memory.search("date format", limit=5)

# Get injected context for LLM
context = memory.inject_context(session)
# Returns: "User prefers DD/MM/YYYY date format\n..."

# End session (auto-save)
memory.end_session(session)
```

### 9.2 CLI Commands

```bash
# Initialize memory system
claw-mem init --workspace ~/.openclaw/workspace

# Start session
claw-mem session start session_001

# Store memory
claw-mem store "User prefers Chinese" --type semantic --tags preference,language

# Search memory
claw-mem search "date format" --limit 10

# Export memory
claw-mem export --format json --output backup.json

# Import memory
claw-mem import --file backup.json

# End session
claw-mem session end session_001

# Show stats
claw-mem stats
```

### 9.3 OpenClaw Plugin API

```python
# OpenClaw plugin entry point
def setup_plugin(config: dict) -> ClawMemPlugin:
    """Initialize claw-mem as OpenClaw plugin"""
    return ClawMemPlugin(
        workspace=config['workspace'],
        auto_inject=config.get('auto_inject', True),
        pre_flight_checks=config.get('pre_flight_checks', True),
    )

# Plugin hooks
class ClawMemPlugin:
    def on_session_start(self, session_id: str) -> str:
        """Inject memory context at session start"""
        return self.memory.inject_context(session_id)
    
    def on_memory_store(self, content: str, metadata: dict) -> bool:
        """Store memory from conversation"""
        return self.memory.store(content, **metadata)
    
    def on_pre_flight_check(self, operation: str, context: dict) -> bool:
        """Run pre-flight check before operation"""
        passed, message = self.memory.pre_flight_check(operation, context)
        if not passed:
            log_warning(f"Pre-flight check failed: {message}")
        return passed
```

---

## 10. Performance Optimization

### 10.1 Startup Optimization

```python
class StartupOptimizer:
    """Optimize startup by lazy-loading memories"""
    
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.index_built = False
    
    def quick_start(self) -> MemoryManager:
        """Return MemoryManager quickly, build index in background"""
        manager = MemoryManager(self.workspace)
        
        # Start index building in background thread
        threading.Thread(target=self._build_index, args=(manager,), daemon=True).start()
        
        return manager
    
    def _build_index(self, manager: MemoryManager) -> None:
        """Build index in background"""
        memories = manager.storage.load_all_memories()
        manager.index.build(memories)
        self.index_built = True
```

### 10.2 Batch Operations

```python
class BatchMemoryWriter:
    """Batch write memories for better performance"""
    
    def __init__(self, store: MarkdownStore, batch_size: int = 100):
        self.store = store
        self.batch_size = batch_size
        self.pending: List[Memory] = []
    
    def write(self, memory: Memory) -> None:
        self.pending.append(memory)
        if len(self.pending) >= self.batch_size:
            self.flush()
    
    def flush(self) -> None:
        if not self.pending:
            return
        
        # Single write operation for all pending memories
        self.store.write_batch(self.pending)
        self.pending = []
```

---

## 11. Testing Strategy

### 11.1 Test Categories

| Category | Coverage | Tools |
|----------|----------|-------|
| Unit Tests | Core logic | pytest |
| Integration Tests | Storage + Retrieval | pytest + temp files |
| Performance Tests | Latency, throughput | pytest-benchmark |
| End-to-End Tests | Full workflow | pytest + OpenClaw |

### 11.2 Key Test Scenarios

```python
# Test pre-flight check
def test_file_operation_check():
    manager = MemoryManager(workspace=test_workspace)
    
    # Should pass: correct directory
    result = manager.pre_flight_check(
        'file_write',
        {'target_path': '/Users/liantian/workspace/test.md', 'file_type': 'daily_project'}
    )
    assert result.passed
    
    # Should fail: wrong directory
    result = manager.pre_flight_check(
        'file_write',
        {'target_path': '/wrong/dir/test.md', 'file_type': 'daily_project'}
    )
    assert not result.passed

# Test memory retrieval
def test_hybrid_retrieval():
    retriever = HybridRetriever(store)
    
    results = retriever.search("date format", limit=5)
    assert len(results) <= 5
    assert all(isinstance(r, Memory) for r in results)

# Test activation decay
def test_activation_decay():
    decay = ActivationDecay({'episodic': 7, 'semantic': 90, 'procedural': 180})
    
    memory = Memory(..., activation_level=1.0, accessed_at=datetime.now() - timedelta(days=7))
    
    # Episodic should decay significantly
    assert decay.decay(memory, datetime.now()) < 0.5
    
    # Semantic should decay minimally
    memory.memory_type = 'semantic'
    assert decay.decay(memory, datetime.now()) > 0.9
```

---

## 12. Deployment

### 12.1 Package Structure

```
claw-mem/
├── pyproject.toml
├── requirements.txt
├── README.md
├── LICENSE
├── docs/
│   ├── REQUIREMENTS.md
│   ├── ARCHITECTURE.md
│   └── API.md
├── src/claw_mem/
│   ├── __init__.py
│   ├── cli.py
│   └── ...
├── tests/
│   ├── test_memory_manager.py
│   ├── test_storage.py
│   └── ...
└── examples/
    ├── basic_usage.py
    └── openclaw_integration.py
```

### 12.2 Dependencies

```txt
# requirements.txt
rank-bm25>=0.2.2  # BM25 search
cachetools>=5.0.0 # Caching
pytest>=7.0.0     # Testing (dev)
pytest-benchmark  # Benchmarking (dev)
```

**Key Decision**: No external database dependencies. Pure Python + minimal packages.

---

## 13. Future Extensions

### 13.1 Plugin Points

| Extension Point | Description |
|----------------|-------------|
| Custom Retriever | Implement `Retriever` interface |
| Custom Decay Function | Replace Ebbinghaus with custom formula |
| Custom Pre-flight Checks | Register new check functions |
| Custom Storage Backend | Optional: add SQLite/Vector DB if needed |

### 13.2 Planned Features

| Feature | Phase | Description |
|---------|-------|-------------|
| Vector Retrieval | Phase 2 (Optional) | Optional Chroma/FAISS integration |
| Knowledge Graph | Phase 3 | Temporal relationships between memories |
| Multi-Agent Sync | Phase 3 | Share memories across agents |
| Cloud Backup | Phase 3 (Optional) | Optional encrypted cloud sync |

---

## 14. Design Decisions

### 14.1 Why Markdown Only?

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| SQLite | Fast, ACID, queries | External dependency, complex | ❌ |
| **Markdown Only** | **No deps, human-readable, versionable** | **Slower for large datasets** | ✅ |
| Hybrid (SQLite+MD) | Best of both | More complex | ❌ Over-engineering |

**Rationale**: Personal AI assistant doesn't need enterprise-grade databases. Keep it simple.

### 14.2 Why In-Memory Index?

| Consideration | Decision |
|--------------|----------|
| Startup cost | ~1s for 1000 memories (acceptable) |
| Memory usage | ~10MB for 1000 memories (acceptable) |
| Query speed | O(1) for N-gram, O(n) for BM25 (fast enough) |
| **Decision** | **In-memory index, rebuilt on startup** |

### 14.3 Why 3-Layer Architecture?

| Layer | Purpose | Trade-off |
|-------|---------|-----------|
| L1 (Working) | Session context | Memory limit |
| L2 (Short-term) | Recent conversations | 30-day expiry |
| L3 (Long-term) | Permanent knowledge | Slower access |

**Rationale**: Matches human memory structure, balances performance and simplicity.

---

## 15. Migration Path

### 15.1 From Existing OpenClaw Memory

**Existing Format** (already compatible):
```
~/.openclaw/workspace/
├── MEMORY.md
└── memory/
    ├── YYYY-MM-DD.md
    └── skills/
```

**Migration Steps**:
1. No migration needed! Format is already compatible.
2. claw-mem will read existing files on startup.
3. Index is auto-generated from existing memories.

### 15.2 Backup and Restore

```bash
# Backup
claw-mem export --format json --output backup_2026-03-18.json

# Restore
claw-mem import --file backup_2026-03-18.json

# Manual backup (cp command)
cp -r ~/.openclaw/workspace/memory ~/backups/memory_2026-03-18
cp ~/.openclaw/workspace/MEMORY.md ~/backups/
```

---

**Document History**:

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-18 | Friday | Initial draft (Markdown-only architecture) |

---

**Status**: Draft (Pending Peter's Review and Approval)
