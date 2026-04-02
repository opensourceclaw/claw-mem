"""
Integration Tests for claw-mem v1.0.3

Tests the complete integration of:
- Semantic Violation Detector
- Configurable Rule Engine
- Package Name Validation
- Release Title Format Enforcement

License: Apache-2.0
Documentation Standard: 100% English (Apache International Open Source Standard)
"""

import pytest
from pathlib import Path
import sys

# Import from deployed location
sys.path.insert(0, str(Path.home() / '.openclaw' / 'workspace' / 'skills' / 'claw-mem' / 'core'))

from semantic_detector import SemanticViolationDetector
from rule_engine import RuleEngine


class TestSemanticDetectorIntegration:
    """Integration tests for Semantic Detector"""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance"""
        return SemanticViolationDetector()
    
    def test_chinese_detection(self, detector):
        """Test Chinese character detection (Unicode range)"""
        violations = detector.detect_violations("用中文写文档")
        assert len(violations) > 0, "Should detect Chinese characters"
    
    def test_english_content(self, detector):
        """Test English content (should pass)"""
        violations = detector.detect_violations("Write English documentation")
        assert len(violations) == 0, "English content should not trigger violations"
    
    def test_package_name_neorl(self, detector):
        """Test invalid package name: neorl"""
        violations = detector.detect_violations("Create package neorl")
        assert len(violations) > 0, "Should detect neorl"
    
    def test_package_name_neomind(self, detector):
        """Test invalid package name: neomind"""
        violations = detector.detect_violations("Import from neomind")
        assert len(violations) > 0, "Should detect neomind"
    
    def test_package_name_valid(self, detector):
        """Test valid package names"""
        for name in ['claw_rl', 'claw-mem']:
            violations = detector.detect_violations(f"Use {name} package")
            assert len(violations) == 0, f"{name} should be valid"
    
    def test_release_title_valid_dash(self, detector):
        """Test valid release title with dash"""
        is_valid, error = detector.validate_release_title("claw-mem v1.0.3")
        assert is_valid, f"Should be valid: {error}"
    
    def test_release_title_valid_underscore(self, detector):
        """Test valid release title with underscore"""
        is_valid, error = detector.validate_release_title("claw_rl v1.0.3")
        assert is_valid, f"Should be valid: {error}"
    
    def test_release_title_invalid_subtitle(self, detector):
        """Test invalid release title with subtitle"""
        is_valid, error = detector.validate_release_title("NeoMind v1.0.3 - Cool Features")
        assert not is_valid, "Should reject subtitle"
    
    def test_release_title_invalid_colon(self, detector):
        """Test invalid release title with colon"""
        is_valid, error = detector.validate_release_title("Release v1.0.3: Update")
        assert not is_valid, "Should reject colon"


class TestRuleEngineIntegration:
    """Integration tests for Rule Engine"""
    
    @pytest.fixture
    def engine(self):
        """Create rule engine with deployed config"""
        return RuleEngine()
    
    def test_load_default_config(self, engine):
        """Test loading default configuration"""
        assert len(engine.rules) > 0, "Should load default rules"
    
    def test_package_name_violation(self, engine):
        """Test package name violation detection"""
        violations = engine.validate("Create package neorl")
        assert len(violations) > 0, "Should detect package name violation"
    
    def test_language_violation(self, engine):
        """Test language violation detection"""
        violations = engine.validate("Write 中文 documentation")
        assert len(violations) > 0, "Should detect language violation"
    
    def test_valid_text(self, engine):
        """Test valid text"""
        violations = engine.validate("claw-mem v1.0.3 release")
        assert len(violations) == 0, "Valid text should not trigger violations"
    
    def test_hot_reload(self, engine):
        """Test configuration hot-reload"""
        initial_count = len(engine.rules)
        engine.reload_config()
        assert len(engine.rules) == initial_count, "Reload should work"


class TestEndToEndIntegration:
    """End-to-end integration tests"""
    
    def test_complete_workflow(self):
        """Test complete violation detection workflow"""
        detector = SemanticViolationDetector()
        engine = RuleEngine()
        
        # Test 1: Semantic detector catches violations
        violations = detector.detect_violations("Create package neorl")
        assert len(violations) > 0, "Semantic detector should catch violations"
        
        # Test 2: Rule engine catches violations
        violations = engine.validate("Create package neorl")
        assert len(violations) > 0, "Rule engine should catch violations"
        
        # Test 3: Both agree on valid text
        detector_violations = detector.detect_violations("claw-mem v1.0.3")
        engine_violations = engine.validate("claw-mem v1.0.3")
        assert len(detector_violations) == 0, "Detector should allow valid text"
        assert len(engine_violations) == 0, "Engine should allow valid text"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
