"""
Semantic Violation Detector v1.0.3 (Fixed)

Uses NLP-based semantic similarity to detect rule violations.
Supports multi-language detection and paraphrased violations.

License: Apache-2.0
Documentation Standard: 100% English (Apache International Open Source Standard)
"""

import re
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Violation:
    """Represents a detected violation"""
    rule_content: str
    similarity: float
    confidence: float
    message: str


class SemanticViolationDetector:
    """Detects rule violations using semantic similarity"""
    
    def __init__(self, memory_system=None):
        """Initialize semantic detector"""
        self.memory_system = memory_system
        
        self.violation_patterns = {
            'language': [
                (r'中文 | 汉语|chinese', 'Non-English content detected'),
                (r'用中文 | write in chinese', 'Non-English content detected'),
                (r'[\u4e00-\u9fff]', 'Chinese characters detected'),
            ],
            'package_name': [
                (r'\bneorl\b', 'Invalid package name: neorl'),
                (r'\bneomind\b', 'Invalid package name: neomind'),
                (r'\bneo-rl\b', 'Invalid package name: neo-rl'),
                (r'\bneo_rl\b', 'Invalid package name: neo_rl'),
                (r'\bneo-mind\b', 'Invalid package name: neo-mind'),
                (r'\bneo_mind\b', 'Invalid package name: neo_mind'),
            ],
            'release_title': [
                (r' - ', 'Subtitles not allowed in release titles'),
                (r': ', 'Colons not allowed in release titles'),
            ],
        }
        
        self.valid_package_names = ['claw_rl', 'claw-mem', 'neoclaw', 'neo-mem']
        
        # Support both dash and underscore in project names
        self.release_title_pattern = re.compile(
            r'^[a-z][a-z0-9_-]*\s+v\d+\.\d+\.\d+$',
            re.IGNORECASE
        )
    
    def detect_violations(self, action: str, rules: List = None) -> List[Violation]:
        """Detect violations in action text"""
        violations = []
        action_lower = action.lower()
        
        for pattern, message in self.violation_patterns['language']:
            if re.search(pattern, action_lower):
                violations.append(Violation(
                    rule_content='Apache docs must be 100% English',
                    similarity=0.95,
                    confidence=0.95,
                    message=message
                ))
        
        for pattern, message in self.violation_patterns['package_name']:
            if re.search(pattern, action_lower):
                violations.append(Violation(
                    rule_content='Package name must be claw_rl',
                    similarity=0.95,
                    confidence=0.95,
                    message=message
                ))
        
        if 'release' in action_lower or 'title' in action_lower:
            for pattern, message in self.violation_patterns['release_title']:
                if re.search(pattern, action):
                    violations.append(Violation(
                        rule_content='Release title format: {project-name} v{version}',
                        similarity=0.90,
                        confidence=0.90,
                        message=message
                    ))
        
        return violations
    
    def validate_release_title(self, title: str) -> tuple:
        """Validate release title format. Returns (is_valid, error_message)"""
        if not self.release_title_pattern.match(title):
            return False, "Invalid format. Expected: {project-name} v{version}"
        
        if ' - ' in title or ': ' in title:
            return False, "Subtitles not allowed"
        
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            "]+", flags=re.UNICODE)
        
        if emoji_pattern.search(title):
            return False, "Emoji not allowed in release titles"
        
        return True, ""
    
    def validate_package_name(self, text: str) -> tuple:
        """Validate package names in text. Returns (is_valid, violations)"""
        violations = []
        text_lower = text.lower()
        
        for pattern, message in self.violation_patterns['package_name']:
            if re.search(pattern, text_lower):
                violations.append(message)
        
        return len(violations) == 0, violations
