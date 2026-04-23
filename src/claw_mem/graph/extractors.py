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
LLM Extractors - LLM 驱动的事实和概念提取器

支持:
- LLM 驱动的智能提取
- 基于规则的备用提取
- 空提取器（用于测试）
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import re


class BaseExtractor(ABC):
    """提取器基类"""

    @abstractmethod
    def extract_facts(self, text: str) -> List[str]:
        """提取事实"""
        pass

    @abstractmethod
    def extract_concepts(self, text: str) -> List[str]:
        """提取概念"""
        pass


class LLMExtractor(BaseExtractor):
    """LLM 驱动的提取器

    支持多种 LLM 客户端（OpenAI, Anthropic, 本地模型等）。
    无 LLM 时使用基于规则的备用方案。
    """

    def __init__(self, llm_client: Any = None):
        """
        Args:
            llm_client: LLM 客户端（支持 .generate(prompt) 方法）
        """
        self.llm = llm_client

    def extract_facts(self, text: str) -> List[str]:
        """从文本中提取关键事实

        Args:
            text: 输入文本

        Returns:
            List[str]: 事实列表
        """
        if not self.llm:
            return self._extract_facts_rule_based(text)

        prompt = self._build_facts_prompt(text)

        try:
            response = self._call_llm(prompt)
            facts = self._parse_lines(response)
            return facts
        except Exception as e:
            # 降级到规则提取
            return self._extract_facts_rule_based(text)

    def extract_concepts(self, text: str) -> List[str]:
        """从文本中提取核心概念

        Args:
            text: 输入文本

        Returns:
            List[str]: 概念列表
        """
        if not self.llm:
            return self._extract_concepts_rule_based(text)

        prompt = self._build_concepts_prompt(text)

        try:
            response = self._call_llm(prompt)
            concepts = self._parse_lines(response)
            return concepts
        except Exception as e:
            # 降级到规则提取
            return self._extract_concepts_rule_based(text)

    def generate_reflection(self, nodes: List[Any]) -> str:
        """从节点生成反思

        Args:
            nodes: 源节点列表

        Returns:
            str: 反思内容
        """
        if not self.llm:
            return self._generate_reflection_rule_based(nodes)

        prompt = self._build_reflection_prompt(nodes)

        try:
            return self._call_llm(prompt)
        except Exception:
            return self._generate_reflection_rule_based(nodes)

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        if hasattr(self.llm, 'generate'):
            return self.llm.generate(prompt)
        elif hasattr(self.llm, 'chat'):
            return self.llm.chat(prompt)
        else:
            raise ValueError("LLM client must have 'generate' or 'chat' method")

    def _parse_lines(self, response: str) -> List[str]:
        """解析 LLM 响应为行列表"""
        lines = response.strip().split('\n')
        return [line.strip().strip('-* ').strip() for line in lines if line.strip()]

    def _build_facts_prompt(self, text: str) -> str:
        """构建事实提取提示"""
        return f"""从以下文本中提取关键事实。

要求：
1. 每行一个事实
2. 只提取客观事实，不要推断
3. 保持简洁

文本：
{text}

事实列表："""

    def _build_concepts_prompt(self, text: str) -> str:
        """构建概念提取提示"""
        return f"""从以下文本中提取核心概念。

要求：
1. 每行一个概念
2. 提取关键词、主题、实体
3. 保持简洁

文本：
{text}

概念列表："""

    def _build_reflection_prompt(self, nodes: List[Any]) -> str:
        """构建反思生成提示"""
        node_contents = "\n".join([f"- {n.content}" for n in nodes[:10]])
        return f"""基于以下记忆节点，生成一个简短的反思总结：

{node_contents}

反思："""

    def _extract_facts_rule_based(self, text: str) -> List[str]:
        """基于规则的事实提取（备用方案）

        按句子分割文本，提取完整句子作为事实。
        """
        # 按常见分隔符分割
        sentences = re.split(r'[。！？.!?\n]+', text)
        facts = []
        for s in sentences:
            s = s.strip()
            # 过滤太短或太长的
            if 5 < len(s) < 200:
                facts.append(s)
        return facts[:5]  # 最多5个

    def _extract_concepts_rule_based(self, text: str) -> List[str]:
        """基于规则的概念提取（备用方案）

        提取中文词语（2-4字）和英文单词作为概念。
        """
        # 中文词语（2-4字）
        chinese = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)

        # 英文单词（3+字母）
        english = re.findall(r'[a-zA-Z]{3,}', text)

        # 合并去重
        concepts = list(set(chinese + english))
        return concepts[:10]  # 最多10个

    def _generate_reflection_rule_based(self, nodes: List[Any]) -> str:
        """基于规则的反思生成（备用方案）"""
        if not nodes:
            return "无足够信息生成反思"

        # 简单策略：取最新的节点内容
        latest = nodes[-1] if nodes else None
        if latest:
            return f"回顾：{latest.content[:100]}"
        return "无足够信息生成反思"


class DummyExtractor(BaseExtractor):
    """空提取器（用于测试）"""

    def extract_facts(self, text: str) -> List[str]:
        """返回空列表"""
        return []

    def extract_concepts(self, text: str) -> List[str]:
        """返回空列表"""
        return []


class KeywordExtractor(BaseExtractor):
    """关键词提取器（轻量级方案）

    不依赖 LLM，使用关键词提取算法。
    """

    def __init__(self):
        self.stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人',
                         '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
                         'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at'}

    def extract_facts(self, text: str) -> List[str]:
        """使用句子分割提取事实"""
        return LLMExtractor()._extract_facts_rule_based(text)

    def extract_concepts(self, text: str) -> List[str]:
        """提取关键词作为概念"""
        # 移除停用词后提取
        words = re.findall(r'[\u4e00-\u9fa5]{2,4}|[a-zA-Z]{3,}', text)
        concepts = [w for w in words if w not in self.stopwords]
        return list(set(concepts))[:10]


__all__ = [
    'BaseExtractor',
    'LLMExtractor',
    'DummyExtractor',
    'KeywordExtractor',
]
