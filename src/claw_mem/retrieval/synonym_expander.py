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
Synonym Expander for claw-mem v2.9.0

Expands search queries with synonym terms to improve recall.
Supports built-in bilingual (Chinese/English) synonym dictionary and
custom user-defined synonym mappings.
"""

from typing import Dict, List, Set, Optional
import re


# ── Built-in Synonym Dictionary ───────────────────────────────────────────────

BUILTIN_SYNONYMS: Dict[str, List[str]] = {
    # AI / Machine Learning
    "ai": ["人工智能", "ai", "machine learning", "ml", "深度学习", "deep learning"],
    "人工智能": ["人工智能", "ai", "machine learning", "ml", "深度学习", "deep learning"],
    "machine learning": ["machine learning", "ml", "人工智能", "ai", "深度学习"],
    "ml": ["ml", "machine learning", "人工智能", "ai", "深度学习"],
    "deep learning": ["deep learning", "深度学习", "dl", "neural network", "神经网络"],
    "深度学习": ["深度学习", "deep learning", "dl", "neural network", "神经网络"],

    # Model / Framework
    "模型": ["模型", "model", "框架", "framework"],
    "model": ["model", "模型", "framework", "框架"],
    "框架": ["框架", "framework", "架构", "architecture"],
    "framework": ["framework", "框架", "architecture", "架构"],

    # Natural Language Processing
    "nlp": ["nlp", "natural language processing", "自然语言处理", "文本处理"],
    "自然语言处理": ["自然语言处理", "nlp", "natural language processing", "文本处理"],

    # Agent / Assistant
    "agent": ["agent", "代理", "助手", "assistant", "智能体"],
    "代理": ["代理", "agent", "助手", "assistant"],
    "助手": ["助手", "assistant", "agent", "代理"],
    "assistant": ["assistant", "助手", "agent", "代理"],

    # Memory / Storage
    "memory": ["memory", "记忆", "存储", "storage", "缓存", "cache"],
    "记忆": ["记忆", "memory", "存储", "storage"],
    "存储": ["存储", "storage", "memory", "记忆", "保存", "持久化"],
    "storage": ["storage", "存储", "memory", "持久化"],

    # Search / Retrieval
    "搜索": ["搜索", "search", "检索", "retrieval", "查询", "query"],
    "search": ["search", "搜索", "检索", "retrieval", "查询"],
    "检索": ["检索", "retrieval", "search", "搜索", "查询"],
    "retrieval": ["retrieval", "检索", "search", "搜索"],

    # Performance / Optimization
    "性能": ["性能", "performance", "优化", "optimization", "速度", "speed"],
    "performance": ["performance", "性能", "优化", "optimization", "速度"],
    "优化": ["优化", "optimization", "改进", "improvement", "性能"],
    "optimization": ["optimization", "优化", "改进", "improvement"],

    # Error / Bug
    "错误": ["错误", "error", "bug", "问题", "issue", "缺陷"],
    "error": ["error", "错误", "bug", "问题", "issue"],
    "bug": ["bug", "缺陷", "错误", "error", "issue"],

    # Deployment / Release
    "部署": ["部署", "deploy", "发布", "release", "上线"],
    "deploy": ["deploy", "部署", "发布", "release"],
    "发布": ["发布", "release", "部署", "deploy", "上线"],

    # Configuration / Settings
    "配置": ["配置", "config", "设置", "settings", "参数"],
    "config": ["config", "配置", "设置", "settings"],
    "settings": ["settings", "设置", "配置", "config"],

    # Code / Development
    "代码": ["代码", "code", "编程", "开发", "development"],
    "code": ["code", "代码", "编程", "开发"],
    "开发": ["开发", "development", "编程", "coding", "代码"],

    # Testing
    "测试": ["测试", "test", "验证", "verify", "检查"],
    "test": ["test", "测试", "验证", "verify", "检查"],

    # Data
    "数据": ["数据", "data", "信息", "information", "资料"],
    "data": ["data", "数据", "信息", "information"],

    # API
    "api": ["api", "接口", "interface", "端点", "endpoint"],
    "接口": ["接口", "api", "interface", "端点"],

    # OpenClaw specific
    "openclaw": ["openclaw", "open claw", "openc law", "openclaw"],
    "neoclaw": ["neoclaw", "neo claw", "neoc law"],
    "claw-mem": ["claw-mem", "claw mem", "clawmem", "memory system"],
    "claw-rl": ["claw-rl", "claw rl", "clawrl", "learning system"],

    # Common Technology
    "python": ["python", "py", "python3"],
    "javascript": ["javascript", "js", "typescript", "ts"],
    "typescript": ["typescript", "ts", "javascript", "js"],
    "docker": ["docker", "容器", "container"],
    "容器": ["容器", "container", "docker"],

    # Project Neo
    "project neo": ["project neo", "neo project", "neo"],
    "harness": ["harness", "harness engineering"],
}


class SynonymExpander:
    """Query synonym expansion for improved recall.

    Expands query terms using a built-in bilingual synonym dictionary,
    with support for custom user-defined mappings.

    Usage:
        expander = SynonymExpander()
        expanded_query = expander.expand("AI search")
        # -> "AI search 人工智能 machine learning 搜索 retrieval"
    """

    def __init__(self, custom_synonyms: Optional[Dict[str, List[str]]] = None,
                 enabled: bool = True, max_expansions: int = 5):
        """Initialize synonym expander.

        Args:
            custom_synonyms: Additional user-defined synonym mappings
            enabled: Whether expansion is active
            max_expansions: Max unique terms per matched keyword
        """
        self._synonyms = dict(BUILTIN_SYNONYMS)
        self.enabled = enabled
        self.max_expansions = max_expansions

        # Merge custom synonyms
        if custom_synonyms:
            for key, terms in custom_synonyms.items():
                key_lower = key.lower()
                if key_lower in self._synonyms:
                    existing = set(self._synonyms[key_lower])
                    existing.update(t.lower() for t in terms)
                    self._synonyms[key_lower] = list(existing)
                else:
                    self._synonyms[key_lower] = [t.lower() for t in terms]

    def add_synonyms(self, keyword: str, terms: List[str]):
        """Add or extend synonym mappings for a keyword.

        Args:
            keyword: The base keyword to map from
            terms: Synonym terms to add
        """
        key_lower = keyword.lower()
        if key_lower in self._synonyms:
            existing = set(self._synonyms[key_lower])
            existing.update(t.lower() for t in terms if t.lower() != key_lower)
            self._synonyms[key_lower] = list(existing)
        else:
            self._synonyms[key_lower] = [t.lower() for t in terms if t.lower() != key_lower]

    def expand(self, query: str) -> str:
        """Expand query with relevant synonyms.

        Args:
            query: Original search query

        Returns:
            Expanded query string with synonyms appended
        """
        if not self.enabled or not query:
            return query

        query_lower = query.lower()
        expanded_terms: Set[str] = set()

        # Check each keyword in the synonym dictionary
        for keyword, synonyms in self._synonyms.items():
            if keyword in query_lower:
                for syn in synonyms:
                    syn_lower = syn.lower()
                    if syn_lower != keyword and syn_lower not in query_lower:
                        expanded_terms.add(syn)
                        if len(expanded_terms) >= self.max_expansions:
                            break
                if len(expanded_terms) >= self.max_expansions:
                    break

        if expanded_terms:
            return f"{query} {' '.join(list(expanded_terms)[:self.max_expansions])}"

        return query

    def get_synonyms(self, keyword: str) -> List[str]:
        """Get synonyms for a specific keyword.

        Args:
            keyword: Keyword to look up

        Returns:
            List of synonym terms, or empty list if not found
        """
        return self._synonyms.get(keyword.lower(), [])


# Global instance
_synonym_expander: Optional[SynonymExpander] = None


def get_synonym_expander(
    custom_synonyms: Optional[Dict[str, List[str]]] = None,
    enabled: bool = True
) -> SynonymExpander:
    """Get or create global synonym expander instance."""
    global _synonym_expander
    if _synonym_expander is None:
        _synonym_expander = SynonymExpander(
            custom_synonyms=custom_synonyms,
            enabled=enabled
        )
    return _synonym_expander


__all__ = [
    'SynonymExpander',
    'get_synonym_expander',
    'BUILTIN_SYNONYMS',
]
