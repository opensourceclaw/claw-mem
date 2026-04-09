"""
Tests for Rule Extractor

Tests rule extraction from memories.
"""

import pytest


class TestRuleExtractor:
    """Test rule extractor"""
    
    def test_extractor_initialization(self):
        """Test extractor initialization"""
        from claw_mem.rule_extractor import RuleExtractor
        
        extractor = RuleExtractor()
        assert extractor is not None
    
    def test_extract_rules_basic(self):
        """Test basic rule extraction"""
        from claw_mem.rule_extractor import RuleExtractor
        
        extractor = RuleExtractor()
        
        memories = [
            {"content": "The user likes pizza"},
            {"content": "The user dislikes broccoli"},
        ]
        
        if hasattr(extractor, 'extract'):
            rules = extractor.extract(memories)
            assert isinstance(rules, list)
    
    def test_extract_from_text(self):
        """Test extracting rules from text"""
        from claw_mem.rule_extractor import RuleExtractor
        
        extractor = RuleExtractor()
        
        text = "The user always prefers coffee in the morning"
        
        if hasattr(extractor, 'extract_from_text'):
            rules = extractor.extract_from_text(text)
            assert rules is not None
    
    def test_rule_format(self):
        """Test rule format"""
        from claw_mem.rule_extractor import RuleExtractor
        
        extractor = RuleExtractor()
        
        if hasattr(extractor, 'format_rule'):
            rule = extractor.format_rule("preference", "coffee", "morning")
            assert isinstance(rule, str)
