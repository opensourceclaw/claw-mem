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
Query Reconstructor (v4.8.0)

Converts vague/ambiguous/context-dependent search queries into explicit,
retrieval-friendly formulations via LLM or rule-based fallback.

Produces a flat list of reformulated query strings that any retriever
can consume — no coupling to specific retrieval implementations.
"""

import hashlib
import re
from typing import Dict, List, Optional

_STOPWORDS_ZH = {
    "这个", "那个", "哪个", "上次", "最近", "之前", "之前那个", "刚刚",
    "的", "吗", "呢", "了", "吧", "啊", "呀", "哈", "哦", "嗯",
}
_STOPWORDS_EN = {
    "this", "that", "those", "these", "the", "last", "recent", "previous",
    "just", "a", "an", "is", "are", "was", "were",
}
_STOPWORDS = _STOPWORDS_ZH | _STOPWORDS_EN

_STEP_BACK_SYSTEM = (
    "You are a query reformulation assistant. "
    "Your job is to convert specific, context-dependent questions into broad, "
    "general search queries that maximize recall in a memory retrieval system. "
    "Remove time references, pronouns, and conversational fillers. "
    "Output ONLY the reformulated query, no explanation."
)

_VARIANTS_SYSTEM = (
    "You are a query variation generator. "
    "Given a search query, generate semantically equivalent reformulations "
    "that would match the same information in a knowledge base. "
    "Output one query per line, 2-3 lines total, no numbering or explanation."
)

# Regex to strip numbering/prefixes from LLM output lines
_LINE_CLEAN = re.compile(r"^[\d]+[\.\)、\s]\s*")


def _clean_line(line: str) -> str:
    """Remove numbering prefixes like '1. ' or '1) ' from a line."""
    return _LINE_CLEAN.sub("", line.strip()).strip()


def _has_cjk(text: str) -> bool:
    """Check if text contains CJK characters."""
    return bool(re.search(r"[\u4e00-\u9fff\u3040-\u309f\uac00-\ud7af]", text))


class QueryReconstructor:
    """Reformulates vague/ambiguous queries for better retrieval recall.

    Two-phase pipeline:
      1. Step-back: Abstract specific details into a broader search query.
      2. Variants: Generate 2-3 semantically equivalent reformulations.

    LLM is used when available (LLMProvider.generate); rule-based extraction
    serves as a graceful fallback.

    Usage:
        qr = QueryReconstructor(llm_provider=llm)
        queries = qr.reconstruct("上次那个 JWT token 的问题怎么解决的")
        # → ["上次那个 JWT token 的问题怎么解决的",
        #     "JWT token 认证问题解决方案",
        #     "JWT 身份验证 token 错误修复",
        #     "JWT token issue resolution"]
    """

    def __init__(self, llm_provider=None, enable_cache: bool = True):
        """Initialize QueryReconstructor.

        Args:
            llm_provider: LLMProvider instance (optional). If None, only
                          rule-based reconstruction is used.
            enable_cache: Whether to cache reconstruction results by MD5(query).
        """
        self._llm = llm_provider
        self._enable_cache = enable_cache
        self._cache: Dict[str, List[str]] = {}

    def reconstruct(self, query: str) -> List[str]:
        """Reconstruct query into a list of retrieval-friendly strings.

        Returns a list starting with the original query, followed by a
        step-back query (if generated) and 2-3 semantic variants.
        All duplicates are removed while preserving order.

        Args:
            query: Original search query string.

        Returns:
            List of reformulated query strings (deduplicated, order preserved).
        """
        if not query or not query.strip():
            return [query] if query else []

        query = query.strip()
        cache_key = hashlib.md5(query.encode("utf-8")).hexdigest()

        if self._enable_cache and cache_key in self._cache:
            return list(self._cache[cache_key])

        results: List[str] = [query]

        step_back = self._step_back(query)
        if step_back and step_back.lower() != query.lower():
            results.append(step_back)

        variants = self._generate_variants(query)
        for v in variants:
            if v.lower() not in [r.lower() for r in results]:
                results.append(v)

        if self._enable_cache:
            self._cache[cache_key] = list(results)

        return results

    # ── LLM-based reconstruction ────────────────────────────────────────

    def _step_back(self, query: str) -> Optional[str]:
        """Generate a broader, decontextualized version of the query.

        Tries LLM first; falls back to rule-based extraction on failure.
        """
        if self._llm is not None:
            try:
                prompt = (
                    f"Convert this specific question into a broader search query "
                    f"that would help retrieve relevant context: '{query}'\n\n"
                    f"Reply with ONLY the reformulated query, nothing else."
                )
                result = self._llm.generate(
                    prompt, system=_STEP_BACK_SYSTEM, max_tokens=128
                )
                cleaned = result.strip()
                if cleaned and cleaned.lower() != query.lower():
                    return cleaned
            except Exception:
                pass
        return self._rule_step_back(query)

    def _generate_variants(self, query: str, n: int = 3) -> List[str]:
        """Generate N semantically equivalent reformulations.

        Tries LLM first; falls back to SynonymExpander-based rule variants.
        """
        if self._llm is not None:
            try:
                prompt = (
                    f"Generate {n} different ways to phrase this search query. "
                    f"Keep the same meaning: '{query}'\n\n"
                    f"Reply with one query per line, no numbering or explanation."
                )
                result = self._llm.generate(
                    prompt, system=_VARIANTS_SYSTEM, max_tokens=256
                )
                if result and result.strip():
                    lines = [
                        _clean_line(line)
                        for line in result.strip().split("\n")
                        if line.strip() and _clean_line(line).lower() != query.lower()
                    ]
                    if lines:
                        return lines[:n]
            except Exception:
                pass
        return self._rule_variants(query, n)

    # ── Rule-based fallback ─────────────────────────────────────────────

    def _rule_step_back(self, query: str) -> Optional[str]:
        """Rule-based step-back: strip conversational fillers, keep core nouns + verbs.

        Strategy:
          1. Split query into tokens (jieba for CJK, whitespace for ASCII).
          2. Filter out stopwords and short tokens.
          3. Rejoin remaining tokens as the step-back query.
        """
        tokens = self._tokenize(query)
        keywords = [
            t
            for t in tokens
            if t.lower() not in _STOPWORDS and len(t) >= 2
        ]
        if not keywords or keywords == tokens:
            return None
        return " ".join(keywords)

    def _rule_variants(self, query: str, n: int = 3) -> List[str]:
        """Rule-based variants: use SynonymExpander to generate keyword substitutions.

        Strategy:
          1. Extract key tokens from the query.
          2. For each token, look up synonyms via SynonymExpander.
          3. Build variants by replacing tokens with synonyms (limit n).
        """
        from .synonym_expander import BUILTIN_SYNONYMS

        tokens = self._tokenize(query)
        keywords = [t for t in tokens if t.lower() not in _STOPWORDS and len(t) >= 2]

        if not keywords:
            return []

        variants: List[str] = []
        seen: set = set()

        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in BUILTIN_SYNONYMS:
                for syn in BUILTIN_SYNONYMS[kw_lower]:
                    syn_clean = syn.lower()
                    if syn_clean != kw_lower and syn_clean not in seen:
                        variant = query.replace(kw, syn)
                        if variant.lower() != query.lower() and variant not in seen:
                            variants.append(variant)
                            seen.add(variant)
                            if len(variants) >= n:
                                return variants[:n]

        # If no synonym variants generated, try simple word-reorder
        if not variants and len(keywords) >= 2:
            # Generate one variant by reordering the last two keywords
            for i in range(len(keywords) - 1, 0, -1):
                reordered = list(keywords)
                reordered[i], reordered[i - 1] = reordered[i - 1], reordered[i]
                variant = " ".join(reordered)
                if variant.lower() != query.lower():
                    variants.append(variant)
                    break

        return variants[:n]

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text: jieba for CJK, whitespace-split for ASCII."""
        if _has_cjk(text):
            return self._jieba_tokenize(text)
        return text.split()

    @staticmethod
    def _jieba_tokenize(text: str) -> List[str]:
        """Tokenize CJK text using jieba, with fallback to character-level."""
        try:
            import jieba
            return list(jieba.cut(text))
        except ImportError:
            # Fallback: split on whitespace + extract CJK character sequences
            tokens: List[str] = []
            buf = ""
            for ch in text:
                if _has_cjk(ch):
                    if buf:
                        tokens.append(buf)
                        buf = ""
                    tokens.append(ch)
                elif ch.isspace():
                    if buf:
                        tokens.append(buf)
                        buf = ""
                else:
                    buf += ch
            if buf:
                tokens.append(buf)
            return tokens

    def clear_cache(self) -> None:
        """Clear the reconstruction cache."""
        self._cache.clear()


__all__ = ["QueryReconstructor"]
