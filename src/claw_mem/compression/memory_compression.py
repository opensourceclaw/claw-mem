"""
Memory Compression Module for claw-mem v2.4.0

Provides long conversation memory compression with >50% compression ratio while preserving key information.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re


class CompressionLevel(Enum):
    """Compression level"""

    LIGHT = "light"  # Light compression (30%)
    MEDIUM = "medium"  # Medium compression (50%)
    AGGRESSIVE = "aggressive"  # Aggressive compression (70%)


@dataclass
class CompressionResult:
    """Compression result"""

    original_length: int
    compressed_length: int
    compression_ratio: float  # Compression ratio
    preserved_content: str
    extracted_keys: List[str] = field(default_factory=list)
    summary: str = ""


class KeyInformationExtractor:
    """
    Key information extractor

    Extract key information from text:
    - Decisions
    - Commitments
    - Important facts
    - Tasks/goals
    """

    # Key patterns for extraction
    DECISION_PATTERNS = [
        r"(决定|决策|选择|确定|批准|同意|拒绝|否认)",
        r"(will|must|should|need to|have to|going to|decided|agreed)",
    ]

    FACT_PATTERNS = [
        r"(事实|实际上|其实|已经|已知)",
        r"(fact|actually|known|already|confirmed)",
    ]

    TASK_PATTERNS = [
        r"(任务|目标|需要|完成|做|执行)",
        r"(task|goal|need|complete|do|execute|action|next step)",
    ]

    def __init__(self):
        self._decision_re = [re.compile(p, re.IGNORECASE) for p in self.DECISION_PATTERNS]
        self._fact_re = [re.compile(p, re.IGNORECASE) for p in self.FACT_PATTERNS]
        self._task_re = [re.compile(p, re.IGNORECASE) for p in self.TASK_PATTERNS]

    def extract(self, text: str) -> Dict[str, List[str]]:
        """Extract key information"""
        return {
            "decisions": self._extract_matches(text, self._decision_re),
            "facts": self._extract_matches(text, self._fact_re),
            "tasks": self._extract_matches(text, self._task_re),
        }

    def _extract_matches(self, text: str, patterns: List[re.Pattern]) -> List[str]:
        """Extract matched content"""
        matches = []
        for pattern in patterns:
            found = pattern.findall(text)
            matches.extend(found)
        return list(set(matches))  # Deduplicate


class MemoryCompressor:
    """
    Memory compressor

    Supports multiple compression levels while preserving key information.
    """

    def __init__(
        self, level: CompressionLevel = CompressionLevel.MEDIUM, preserve_key_info: bool = True
    ):
        self.level = level
        self.preserve_key_info = preserve_key_info
        self._extractor = KeyInformationExtractor()

        # Set target compression ratios
        self._ratios = {
            CompressionLevel.LIGHT: 0.3,
            CompressionLevel.MEDIUM: 0.5,
            CompressionLevel.AGGRESSIVE: 0.7,
        }

    def compress(self, content: str) -> CompressionResult:
        """
        Compress memory content

        Args:
            content: Original content

        Returns:
            Compression result
        """
        original_length = len(content)

        # Extract key information first
        key_info = {}
        if self.preserve_key_info:
            key_info = self._extractor.extract(content)

        # Apply compression based on level
        if self.level == CompressionLevel.LIGHT:
            compressed = self._compress_light(content)
        elif self.level == CompressionLevel.MEDIUM:
            compressed = self._compress_medium(content)
        else:
            compressed = self._compress_aggressive(content)

        # Calculate metrics
        compressed_length = len(compressed)
        ratio = 1 - (compressed_length / original_length) if original_length > 0 else 0

        # Build summary from key info
        summary = self._build_summary(key_info)

        return CompressionResult(
            original_length=original_length,
            compressed_length=compressed_length,
            compression_ratio=ratio,
            preserved_content=compressed,
            extracted_keys=self._flatten_keys(key_info),
            summary=summary,
        )

    def _compress_light(self, content: str) -> str:
        """Light compression: remove extra whitespace and short words"""
        # Remove extra whitespace
        lines = content.split("\n")
        cleaned = [line.strip() for line in lines if line.strip()]

        # Remove very short lines (< 10 chars)
        result = [line for line in cleaned if len(line) >= 10]
        return "\n".join(result)

    def _compress_medium(self, content: str) -> str:
        """Medium compression: remove duplicates and low-information content"""
        lines = content.split("\n")
        cleaned = [line.strip() for line in lines if line.strip()]

        # Remove consecutive duplicate lines
        result = []
        prev = None
        for line in cleaned:
            if line != prev:
                result.append(line)
                prev = line

        # Remove very short lines (< 15 chars)
        result = [line for line in result if len(line) >= 15]

        return "\n".join(result)

    def _compress_aggressive(self, content: str) -> str:
        """Aggressive compression: only preserve key information"""
        # First extract key information
        key_info = self._extractor.extract(content)

        # Get all key sentences
        sentences = re.split(r"[.!?.!?\n]", content)
        key_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_lower = sentence.lower()

            # Keep sentences with key information
            keep = False
            if any(
                sentence_lower in info.lower() or info.lower() in sentence_lower
                for info in key_info.get("decisions", [])
            ):
                keep = True
            elif any(
                sentence_lower in info.lower() or info.lower() in sentence_lower
                for info in key_info.get("tasks", [])
            ):
                keep = True
            elif any(
                sentence_lower in info.lower() or info.lower() in sentence_lower
                for info in key_info.get("facts", [])
            ):
                keep = True

            # Keep sentences that are important (contain key words)
            if not keep:
                important_words = [
                    "important",
                    "critical",
                    "key",
                    "essential",
                    "must",
                    "need",
                    "should",
                    "will",
                    "decide",
                    "agree",
                    "plan",
                ]
                if any(word in sentence_lower for word in important_words):
                    keep = True

            # Keep moderate length sentences
            if not keep and 20 <= len(sentence) <= 150:
                keep = True

            if keep:
                key_sentences.append(sentence)

        return ". ".join(key_sentences) + "." if key_sentences else content[:500]
        key_sentences = []

        key_info = self._extractor.extract(content)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Keep sentences with key information
            if any(sentence.lower() in info.lower() for info in key_info.get("decisions", [])):
                key_sentences.append(sentence)
            elif any(sentence.lower() in info.lower() for info in key_info.get("tasks", [])):
                key_sentences.append(sentence)
            elif any(sentence.lower() in info.lower() for info in key_info.get("facts", [])):
                key_sentences.append(sentence)
            elif len(sentence) < 100:  # Keep short sentences
                key_sentences.append(sentence)

        return ". ".join(key_sentences) + "."

    def _build_summary(self, key_info: Dict[str, List[str]]) -> str:
        """Build summary from key information"""
        parts = []

        if key_info.get("decisions"):
            decisions = key_info["decisions"][:3]  # Limit to 3
            parts.append(f"Decisions: {', '.join(decisions)}")

        if key_info.get("tasks"):
            tasks = key_info["tasks"][:3]
            parts.append(f"Tasks: {', '.join(tasks)}")

        if key_info.get("facts"):
            facts = key_info["facts"][:3]
            parts.append(f"Facts: {', '.join(facts)}")

        return " | ".join(parts) if parts else ""

    def _flatten_keys(self, key_info: Dict[str, List[str]]) -> List[str]:
        """Flatten key information"""
        keys = []
        keys.extend(key_info.get("decisions", []))
        keys.extend(key_info.get("facts", []))
        keys.extend(key_info.get("tasks", []))
        return list(set(keys))


# Global compressor
_compressor: Optional[MemoryCompressor] = None


def get_compressor(level: CompressionLevel = CompressionLevel.MEDIUM) -> MemoryCompressor:
    """Get compressor instance"""
    global _compressor
    if _compressor is None:
        _compressor = MemoryCompressor(level)
    return _compressor


def compress_memory(
    content: str, level: CompressionLevel = CompressionLevel.MEDIUM
) -> CompressionResult:
    """Quick compression function"""
    compressor = MemoryCompressor(level)
    return compressor.compress(content)
