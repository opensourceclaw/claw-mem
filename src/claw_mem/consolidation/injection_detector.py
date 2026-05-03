"""
claw-mem v2.10.0 - Injection Detector

Detects and isolates prompt injection attempts before they reach
the weight consolidation layer.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class InjectionResult:
    """Result of injection detection."""
    is_injection: bool
    confidence: float
    patterns_matched: List[str] = field(default_factory=list)
    sanitized_content: str = ""


class InjectionDetector:
    """Detect prompt injection attempts in experience content.

    Usage:
        detector = InjectionDetector()
        result = detector.scan("Ignore previous instructions...")
        if result.is_injection:
            # Block this experience from consolidation
            pass
    """

    INJECTION_PATTERNS = [
        # Direct instruction override
        r"(?:ignore|forget|disregard).*(?:instructions?|prompts?|rules?)",
        r"(?:you\s+are|act\s+as|pretend\s+to\s+be|you\s+must)\s+now",
        r"output\s+(?:the\s+)?(?:system\s+)?(?:prompt|instructions?)",
        r"(?:new\s+instructions?|new\s+prompts?)\s*(?::|are|is)",
        # Role manipulation
        r"(?:system\s*:\s*|\[system\])",
        r"(?:<\|(?:system|im_start|im_end)\|>)",
        # Data exfiltration
        r"(?:print|output|display|show|dump)\s+(?:all\s+)?(?:your\s+)?(?:instructions?|prompts?|rules?|system\s+message)",
        r"(?:what\s+is\s+your\s+(?:system\s+)?(?:prompt|instructions?|rules?))",
        # Weight manipulation
        r"(?:modify|change|alter|update)\s+(?:your\s+)?(?:weights?|parameters?|learning)",
        r"(?:bypass|override|skip)\s+(?:the\s+)?(?:filter|detector|classifier|consolidation)",
    ]

    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold

    def scan(self, content: str) -> InjectionResult:
        """Scan content for injection patterns.

        Args:
            content: Experience content to scan

        Returns:
            InjectionResult with detection status
        """
        if not content:
            return InjectionResult(is_injection=False, confidence=0.0)

        content_lower = content.lower()
        matched = []

        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, content_lower):
                matched.append(pattern)

        confidence = min(1.0, len(matched) * 0.5)

        return InjectionResult(
            is_injection=confidence >= self.threshold,
            confidence=confidence,
            patterns_matched=matched,
            sanitized_content="" if confidence >= self.threshold else content,
        )

    def is_safe(self, content: str) -> bool:
        """Quick check: is content safe for consolidation?"""
        return not self.scan(content).is_injection
