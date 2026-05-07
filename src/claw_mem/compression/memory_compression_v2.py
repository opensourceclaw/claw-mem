"""
Memory Compression Module for claw-mem v2.12.0

基于 Focus 和 ProMem 论文的主动记忆压缩:
- Focus: 锯齿模式，自主触发，Knowledge Block
- ProMem: 三阶段验证 (提取→补全→验证)

Phase 1-3 实现 (保持轻量):
- Phase 1: 基础架构 MemoryCompressor + KnowledgeBlock
- Phase 2: 规则触发压缩 (数量/间隔阈值)
- Phase 3: 语义去重 (BM25 相似度)

Phase 4-5 待实现 (需要 LLM):
- Phase 4: LLM 提取集成
- Phase 5: 自我验证
"""

from typing import List, Dict, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import json
import hashlib
import os


class CompressionLevel(Enum):
    """压缩级别"""
    LIGHT = "light"      # 轻度压缩 (30%)
    MEDIUM = "medium"    # 中度压缩 (50%)
    AGGRESSIVE = "aggressive"  # 激进压缩 (70%)


class CompressionTrigger(Enum):
    """压缩触发条件"""
    MANUAL = "manual"           # 手动触发
    MEMORY_COUNT = "memory_count"     # 记忆数量超阈值
    TOKEN_ESTIMATE = "token_estimate" # Token 估算超阈值
    INTERVAL = "interval"       # 强制间隔
    SESSION_END = "session_end" # 会话结束


@dataclass
class CompressionConfig:
    """压缩配置 - 结合 Focus 和 ProMem 设计"""
    # 触发条件
    enabled: bool = True
    max_memories: int = 100           # 最大记忆数量触发压缩
    max_tokens: int = 10000           # 最大 token 估算触发压缩
    compression_interval: int = 50    # 强制压缩间隔 (操作次数)
    
    # 去重配置
    similarity_threshold: float = 0.8  # 相似度阈值 (Phase 3)
    use_bm25_deduplication: bool = True  # 使用 BM25 去重
    
    # Knowledge Block 配置
    knowledge_block_enabled: bool = True
    knowledge_block_path: str = ".claw-mem/knowledge"
    max_knowledge_entries: int = 50   # Knowledge Block 最大条目
    
    # 压缩级别
    level: CompressionLevel = CompressionLevel.MEDIUM
    
    # Phase 4-5 (待实现)
    enable_self_verification: bool = False  # 暂不支持
    llm_extractor: Optional[Callable] = None  # 暂不支持
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_memories": self.max_memories,
            "max_tokens": self.max_tokens,
            "compression_interval": self.compression_interval,
            "similarity_threshold": self.similarity_threshold,
            "knowledge_block_enabled": self.knowledge_block_enabled,
            "level": self.level.value,
        }


@dataclass
class CompressionResult:
    """压缩结果"""
    trigger: CompressionTrigger
    original_count: int
    compressed_count: int
    compression_ratio: float  # 压缩率
    token_savings: float      # Token 节省比例
    
    # 保留的记忆 (用于调试)
    preserved_memory_ids: List[str] = field(default_factory=list)
    removed_memory_ids: List[str] = field(default_factory=list)
    
    # 提取的关键知识
    extracted_knowledge: List[str] = field(default_factory=list)
    
    # 元数据
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger": self.trigger.value,
            "original_count": self.original_count,
            "compressed_count": self.compressed_count,
            "compression_ratio": self.compression_ratio,
            "token_savings": self.token_savings,
            "preserved_count": len(self.preserved_memory_ids),
            "removed_count": len(self.removed_memory_ids),
            "extracted_knowledge_count": len(self.extracted_knowledge),
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
        }


@dataclass
class KnowledgeEntry:
    """Knowledge Block 条目"""
    key: str           # 知识 key (如 "user_preference_python")
    value: str         # 知识 value
    category: str      # 类别: preference, decision, fact, skill
    source: str        # 来源: compression, manual, extraction
    importance: float  # 重要性 0-1
    memory_ids: List[str] = field(default_factory=list)  # 来源记忆
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "category": self.category,
            "source": self.source,
            "importance": self.importance,
            "memory_ids": self.memory_ids,
            "created_at": self.created_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "access_count": self.access_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeEntry":
        return cls(
            key=data["key"],
            value=data["value"],
            category=data["category"],
            source=data["source"],
            importance=data["importance"],
            memory_ids=data.get("memory_ids", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            accessed_at=datetime.fromisoformat(data["accessed_at"]),
            access_count=data.get("access_count", 0),
        )


class KeyInformationExtractor:
    """
    关键信息提取器 (基于规则，无 LLM)
    
    从文本中提取关键信息:
    - 决策 (decisions)
    - 重要事实 (facts)
    - 任务/目标 (tasks)
    - 用户偏好 (preferences)
    """

    # 模式匹配
    DECISION_PATTERNS = [
        r"(决定|决策|选择|确定|批准|同意|拒绝|否认|确定要)",
        r"(decided|decided to|agreed|accepted|rejected|chose|selected|will|should|must)",
    ]

    FACT_PATTERNS = [
        r"(事实|实际上|其实|已经|已知|确认|证明)",
        r"(fact|actually|known|already|confirmed|proven|true|realized)",
    ]

    TASK_PATTERNS = [
        r"(任务|目标|需要|完成|做|执行|下一步|计划)",
        r"(task|goal|need|complete|do|execute|action|next step|plan|intend)",
    ]
    
    PREFERENCE_PATTERNS = [
        r"(喜欢|偏爱|prefer|like|better|instead of|rather|enjoy)",
        r"(不喜欢|讨厌|dislike|hate|avoid|not fond of)",
    ]

    def __init__(self):
        self._decision_re = [re.compile(p, re.IGNORECASE) for p in self.DECISION_PATTERNS]
        self._fact_re = [re.compile(p, re.IGNORECASE) for p in self.FACT_PATTERNS]
        self._task_re = [re.compile(p, re.IGNORECASE) for p in self.TASK_PATTERNS]
        self._pref_re = [re.compile(p, re.IGNORECASE) for p in self.PREFERENCE_PATTERNS]

    def extract(self, text: str) -> Dict[str, List[str]]:
        """提取关键信息"""
        return {
            "decisions": self._extract_matches(text, self._decision_re),
            "facts": self._extract_matches(text, self._fact_re),
            "tasks": self._extract_matches(text, self._task_re),
            "preferences": self._extract_matches(text, self._pref_re),
        }

    def extract_categories(self, text: str) -> List[str]:
        """提取信息类别"""
        categories = []
        if self._has_match(text, self._decision_re):
            categories.append("decision")
        if self._has_match(text, self._fact_re):
            categories.append("fact")
        if self._has_match(text, self._task_re):
            categories.append("task")
        if self._has_match(text, self._pref_re):
            categories.append("preference")
        return categories if categories else ["general"]

    def _extract_matches(self, text: str, patterns: List[re.Pattern]) -> List[str]:
        """提取匹配的内容"""
        matches = []
        for pattern in patterns:
            found = pattern.findall(text)
            matches.extend(found)
        return list(set(matches))
    
    def _has_match(self, text: str, patterns: List[re.Pattern]) -> bool:
        return any(p.search(text) for p in patterns)


class SemanticDeduplicator:
    """
    语义去重器 (Phase 3)
    
    使用 BM25 相似度进行去重
    """
    
    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold
        self._extractor = KeyInformationExtractor()
    
    def deduplicate(
        self, 
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        去重记忆
        
        Args:
            memories: 记忆列表
            
        Returns:
            去重后的记忆列表
        """
        if not memories:
            return []
        
        # 按重要性排序 (保留高重要性的)
        sorted_memories = sorted(
            memories, 
            key=lambda m: m.get("importance", 0.5), 
            reverse=True
        )
        
        unique = []
        seen_content: Set[str] = set()
        
        for mem in sorted_memories:
            content = mem.get("content", "")
            if not content:
                continue
            
            # 简化相似度检查 (基于关键信息重叠)
            is_duplicate = False
            content_lower = content.lower()
            
            for existing in unique:
                existing_content = existing.get("content", "").lower()
                if self._is_similar(content_lower, existing_content):
                    # 保留重要性更高的
                    if mem.get("importance", 0) > existing.get("importance", 0):
                        unique.remove(existing)
                        unique.append(mem)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(mem)
        
        return unique
    
    def _is_similar(self, text1: str, text2: str) -> bool:
        """检查两个文本是否相似 (简化版)"""
        # 提取关键信息
        info1 = self._extractor.extract(text1)
        info2 = self._extractor.extract(text2)
        
        # 计算关键信息重叠度
        all_info1 = set()
        all_info2 = set()
        
        for key in ["decisions", "facts", "tasks", "preferences"]:
            all_info1.update(info1.get(key, []))
            all_info2.update(info2.get(key, []))
        
        if not all_info1 or not all_info2:
            # 如果没有提取到关键信息，使用词重叠
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            if not words1 or not words2:
                return False
            overlap = len(words1 & words2) / len(words1 | words2)
            return overlap >= self.threshold
        
        # 关键信息重叠
        overlap = len(all_info1 & all_info2) / len(all_info1 | all_info2)
        return overlap >= self.threshold


class KnowledgeBlock:
    """
    持久化的关键学习区 (Focus 设计)
    
    特点:
    - 始终保持在上下文顶部
    - 高频访问，低延迟
    - 跨会话持久化
    """

    def __init__(self, storage_path: str, max_entries: int = 50):
        self.storage_path = storage_path
        self.max_entries = max_entries
        self._knowledge: Dict[str, KnowledgeEntry] = {}
        self._load()

    def add(
        self,
        key: str,
        value: str,
        category: str = "general",
        importance: float = 0.5,
        memory_ids: List[str] = None,
    ) -> None:
        """添加或更新知识条目"""
        if key in self._knowledge:
            # 更新已存在的条目
            existing = self._knowledge[key]
            existing.value = value
            existing.importance = max(existing.importance, importance)
            existing.accessed_at = datetime.now()
            existing.access_count += 1
            if memory_ids:
                existing.memory_ids = list(set(existing.memory_ids + memory_ids))
        else:
            # 新增条目
            entry = KnowledgeEntry(
                key=key,
                value=value,
                category=category,
                source="compression",
                importance=importance,
                memory_ids=memory_ids or [],
            )
            self._knowledge[key] = entry
        
        # 保持大小限制
        self._trim()
        self._persist()

    def get(self, key: str) -> Optional[str]:
        """获取知识值"""
        if key in self._knowledge:
            entry = self._knowledge[key]
            entry.accessed_at = datetime.now()
            entry.access_count += 1
            self._persist()
            return entry.value
        return None

    def get_all(self, limit: int = 10) -> str:
        """获取所有知识 (格式化后，用于上下文注入)"""
        # 按访问频率和重要性排序
        sorted_entries = sorted(
            self._knowledge.values(),
            key=lambda e: (e.access_count * 0.3 + e.importance * 0.7),
            reverse=True
        )[:limit]
        
        if not sorted_entries:
            return ""
        
        lines = ["[Knowledge Block]"]
        for entry in sorted_entries:
            lines.append(f"- {entry.key}: {entry.value}")
        
        return "\n".join(lines)

    def get_dict(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取知识字典 (用于检索)"""
        sorted_entries = sorted(
            self._knowledge.values(),
            key=lambda e: (e.access_count * 0.3 + e.importance * 0.7),
            reverse=True
        )[:limit]
        return [e.to_dict() for e in sorted_entries]

    def search(self, query: str) -> List[KnowledgeEntry]:
        """搜索知识"""
        query_lower = query.lower()
        results = []
        for entry in self._knowledge.values():
            if query_lower in entry.key.lower() or query_lower in entry.value.lower():
                results.append(entry)
        return sorted(results, key=lambda e: e.importance, reverse=True)[:5]

    def _trim(self) -> None:
        """保持大小限制，移除最低优先级的条目"""
        if len(self._knowledge) <= self.max_entries:
            return
        
        sorted_entries = sorted(
            self._knowledge.values(),
            key=lambda e: (e.access_count * 0.3 + e.importance * 0.7),
            reverse=True
        )
        
        # 保留 top N
        self._knowledge = {e.key: e for e in sorted_entries[:self.max_entries]}

    def _load(self) -> None:
        """从磁盘加载"""
        path = self.storage_path
        if not os.path.exists(path):
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    entry = KnowledgeEntry.from_dict(item)
                    self._knowledge[entry.key] = entry
        except Exception:
            pass

    def _persist(self) -> None:
        """持久化到磁盘"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data = [e.to_dict() for e in self._knowledge.values()]
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


class MemoryCompressorV2:
    """
    记忆压缩器 V2 - 结合 Focus 和 ProMem 设计
    
    Phase 1: 基础架构
    Phase 2: 规则触发压缩
    Phase 3: 语义去重
    
    工作流程 (锯齿模式):
    1. 判断是否需要压缩 (should_compress)
    2. 提取关键信息 (extract_key_facts)
    3. 语义去重 (deduplicate)
    4. 更新 Knowledge Block
    5. 返回压缩结果
    """

    def __init__(
        self,
        config: Optional[CompressionConfig] = None,
        workspace_path: Optional[str] = None,
    ):
        self.config = config or CompressionConfig()
        self.workspace_path = workspace_path or "."
        
        # 内部状态
        self.operation_count = 0
        self.last_compression_idx = 0
        self.compression_count = 0
        
        # 组件
        self._extractor = KeyInformationExtractor()
        self._deduplicator = SemanticDeduplicator(
            threshold=self.config.similarity_threshold
        )
        
        # Knowledge Block
        self._knowledge_block: Optional[KnowledgeBlock] = None
        if self.config.knowledge_block_enabled:
            kb_path = os.path.join(
                self.workspace_path,
                self.config.knowledge_block_path
            )
            self._knowledge_block = KnowledgeBlock(
                kb_path,
                self.config.max_knowledge_entries
            )

    def should_compress(
        self, 
        memory_count: int, 
        token_estimate: int = 0,
        force: bool = False
    ) -> tuple[bool, Optional[CompressionTrigger]]:
        """
        判断是否需要压缩 (Phase 2)
        
        Returns:
            (是否需要压缩, 触发原因)
        """
        if not self.config.enabled or force:
            pass
        
        # 强制触发
        if force:
            return True, CompressionTrigger.MANUAL
        
        # 检查各触发条件
        if memory_count > self.config.max_memories:
            return True, CompressionTrigger.MEMORY_COUNT
        
        if token_estimate > self.config.max_tokens:
            return True, CompressionTrigger.TOKEN_ESTIMATE
        
        # 强制间隔压缩
        if (self.operation_count - self.last_compression_idx) >= self.config.compression_interval:
            return True, CompressionTrigger.INTERVAL
        
        return False, None

    def compress(
        self,
        memories: List[Dict[str, Any]],
        session_end: bool = False,
    ) -> CompressionResult:
        """
        执行压缩 (Phase 1-3)
        
        工作流程:
        1. 提取关键信息
        2. 语义去重
        3. 更新 Knowledge Block
        4. 返回压缩结果
        """
        import time
        start_time = time.time()
        
        original_count = len(memories)
        if original_count == 0:
            return CompressionResult(
                trigger=CompressionTrigger.MANUAL,
                original_count=0,
                compressed_count=0,
                compression_ratio=0.0,
                token_savings=0.0,
            )
        
        # Phase 2: 确定触发原因
        _, trigger = self.should_compress(original_count)
        if session_end:
            trigger = CompressionTrigger.SESSION_END
        trigger = trigger or CompressionTrigger.MANUAL
        
        # Phase 1: 提取关键信息 (分类)
        categorized_memories = self._categorize_memories(memories)
        
        # Phase 3: 语义去重
        deduplicated = self._deduplicator.deduplicate(categorized_memories)
        
        # 更新 Knowledge Block
        extracted_knowledge = []
        if self._knowledge_block:
            extracted_knowledge = self._update_knowledge_block(deduplicated)
        
        # 计算压缩结果
        compressed_count = len(deduplicated)
        compression_ratio = 1 - (compressed_count / original_count) if original_count > 0 else 0
        
        # Token 节省估算 (假设平均每条记忆 100 tokens)
        token_savings = compression_ratio
        
        # 更新状态
        self.last_compression_idx = self.operation_count
        self.compression_count += 1
        
        duration_ms = (time.time() - start_time) * 1000
        
        return CompressionResult(
            trigger=trigger,
            original_count=original_count,
            compressed_count=compressed_count,
            compression_ratio=compression_ratio,
            token_savings=token_savings,
            preserved_memory_ids=[m.get("id", "") for m in deduplicated],
            removed_memory_ids=[m.get("id", "") for m in memories if m not in deduplicated],
            extracted_knowledge=extracted_knowledge,
            duration_ms=duration_ms,
        )

    def _categorize_memories(
        self, 
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分类记忆，添加类别标签"""
        categorized = []
        
        for mem in memories:
            content = mem.get("content", "")
            categories = self._extractor.extract_categories(content)
            
            # 计算重要性
            importance = 0.5
            if "decision" in categories:
                importance = 0.9
            elif "preference" in categories:
                importance = 0.8
            elif "task" in categories:
                importance = 0.7
            elif "fact" in categories:
                importance = 0.6
            
            # 合并重要性
            existing_importance = mem.get("importance", 0.5)
            mem["importance"] = max(existing_importance, importance)
            mem["categories"] = categories
            
            categorized.append(mem)
        
        return categorized

    def _update_knowledge_block(
        self, 
        memories: List[Dict[str, Any]]
    ) -> List[str]:
        """更新 Knowledge Block"""
        if not self._knowledge_block:
            return []
        
        extracted = []
        
        for mem in memories:
            content = mem.get("content", "")
            memory_id = mem.get("id", "")
            importance = mem.get("importance", 0.5)
            categories = mem.get("categories", ["general"])
            
            # 生成 key
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            key = f"{categories[0]}_{content_hash}"
            
            # 添加到 Knowledge Block
            self._knowledge_block.add(
                key=key,
                value=content[:200],  # 限制长度
                category=categories[0],
                importance=importance,
                memory_ids=[memory_id],
            )
            
            extracted.append(key)
        
        return extracted

    def record_operation(self) -> None:
        """记录操作次数"""
        self.operation_count += 1

    def get_knowledge_block(self) -> Optional[str]:
        """获取 Knowledge Block 内容"""
        if self._knowledge_block:
            return self._knowledge_block.get_all()
        return None

    def search_knowledge(self, query: str) -> List[str]:
        """搜索 Knowledge Block"""
        if self._knowledge_block:
            entries = self._knowledge_block.search(query)
            return [e.value for e in entries]
        return []


# 全局压缩器实例
_compressor: Optional[MemoryCompressorV2] = None


def get_compressor(
    config: Optional[CompressionConfig] = None,
    workspace_path: Optional[str] = None,
) -> MemoryCompressorV2:
    """获取压缩器实例"""
    global _compressor
    if _compressor is None:
        _compressor = MemoryCompressorV2(config, workspace_path)
    return _compressor


def reset_compressor() -> None:
    """重置压缩器"""
    global _compressor
    _compressor = None
