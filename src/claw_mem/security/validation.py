"""
Write Validator (MVP Version)

Validates memory write requests, rejects unsafe content.
"""

import re
from typing import List


class WriteValidator:
    """
    Write Validator
    
    MVP version uses rule-based matching. Semantic analysis will be added in future iterations.
    """
    
    # Unsafe patterns list
    UNSAFE_PATTERNS = [
        r"ignore.*instruction",  # Ignore instructions
        r"override.*memory",     # Override memory
        r"delete.*file",         # Delete files
        r"execute.*code",        # Execute code
        r"system:",              # System prompt injection
        r"<\|startoftext\|>",   # Special tokens
        r"act as.*system",       # Role-playing attacks
    ]
    
    def __init__(self):
        """Initialize validator"""
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.UNSAFE_PATTERNS
        ]
    
    def validate(self, content: str) -> bool:
        """
        Validate memory content safety
        
        Args:
            content: Memory content
            
        Returns:
            bool: Safety status
        """
        # Check empty content
        if not content or len(content.strip()) == 0:
            return False
        
        # Check unsafe patterns
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                return False
        
        # Check length (prevent overflow)
        if len(content) > 10000:
            return False
        
        return True
    
    def get_rejection_reason(self, content: str) -> str:
        """
        Get rejection reason
        
        Args:
            content: Memory content
            
        Returns:
            str: Rejection reason
        """
        if not content or len(content.strip()) == 0:
            return "Content is empty"
        
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(content):
                return f"Contains unsafe pattern: {self.UNSAFE_PATTERNS[i]}"
        
        if len(content) > 10000:
            return "Content too long (max 10000 characters)"
        
        return "Unknown reason"
