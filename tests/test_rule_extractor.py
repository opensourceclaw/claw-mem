"""
Tests for Rule Extractor

Tests rule extraction from memories.
"""

import pytest
from pathlib import Path
import tempfile


@pytest.fixture
def workspace():
    """Provide a temporary workspace"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestRuleExtractor:
    """Test rule extractor"""
    
    def test_extractor_initialization(self, workspace):
        """Test extractor initialization"""
        from claw_mem.rule_extractor import RuleExtractor
        
        extractor = RuleExtractor(workspace)
        assert extractor is not None
    
    def test_extract_rules_basic(self, workspace):
        """Test basic rule extraction"""
        from claw_mem.rule_extractor import RuleExtractor
        
        extractor = RuleExtractor(workspace)
        
        conversation = "do not create files to /tmp/"
        
        rule = extractor.extract(conversation)
        assert rule is not None
        assert rule.rule_type in ["FORBIDDEN_PATH", "FORBIDDEN_TOOL", "PREFERENCE", "REQUIRE_ORDER"]
    
    def test_extract_from_text(self, workspace):
        """Test extracting rules from text"""
        from claw_mem.rule_extractor import RuleExtractor
        
        extractor = RuleExtractor(workspace)
        
        text = "I prefer use Chinese for reply"
        
        rule = extractor.extract(text)
        assert rule is not None
        assert rule.rule_type == "PREFERENCE"
    
    def test_rule_format(self, workspace):
        """Test rule format"""
        from claw_mem.rule_extractor import RuleExtractor
        
        extractor = RuleExtractor(workspace)
        assert extractor.rules_file is not None
