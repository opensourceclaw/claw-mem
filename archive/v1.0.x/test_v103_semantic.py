"""
Tests for Semantic Detector v1.0.3

License: Apache-2.0
Documentation Standard: 100% English (Apache International Open Source Standard)
"""

import pytest
from semantic_detector import SemanticViolationDetector, Violation


class TestSemanticViolationDetector:
    """Test semantic violation detector"""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance"""
        return SemanticViolationDetector()
    
    def test_language_violation_english(self, detector):
        """Test English content (should pass)"""
        violations = detector.detect_violations("Write English documentation")
        assert len(violations) == 0
    
    def test_language_violation_chinese(self, detector):
        """Test Chinese content (should fail)"""
        violations = detector.detect_violations("用中文写文档")
        assert len(violations) > 0
        assert any('Non-English' in v.message for v in violations)
    
    def test_package_name_violation_neorl(self, detector):
        """Test invalid package name: neorl"""
        violations = detector.detect_violations("Create package neorl")
        assert len(violations) > 0
        assert any('neorl' in v.message for v in violations)
    
    def test_package_name_violation_neomind(self, detector):
        """Test invalid package name: neomind"""
        violations = detector.detect_violations("Import from neomind")
        assert len(violations) > 0
        assert any('neomind' in v.message for v in violations)
    
    def test_package_name_valid(self, detector):
        """Test valid package name: claw_rl"""
        violations = detector.detect_violations("Use claw_rl package")
        assert len(violations) == 0
    
    def test_release_title_valid(self, detector):
        """Test valid release title"""
        is_valid, error = detector.validate_release_title("claw-mem v1.0.3")
        assert is_valid == True
        assert error == ""
    
    def test_release_title_invalid_subtitle(self, detector):
        """Test invalid release title with subtitle"""
        is_valid, error = detector.validate_release_title("NeoMind v1.0.3 - Cool Features")
        assert is_valid == False
        assert 'Subtitles' in error
    
    def test_release_title_invalid_colon(self, detector):
        """Test invalid release title with colon"""
        is_valid, error = detector.validate_release_title("Release v1.0.3: Update")
        assert is_valid == False
    
    def test_release_title_invalid_format(self, detector):
        """Test invalid release title format"""
        is_valid, error = detector.validate_release_title("Version 1.0.3")
        assert is_valid == False
        assert 'Invalid format' in error


class TestRuleEngine:
    """Test rule engine"""
    
    @pytest.fixture
    def engine(self, tmp_path):
        """Create rule engine with temp config"""
        from rule_engine import RuleEngine
        config_path = tmp_path / "rules.json"
        return RuleEngine(str(config_path))
    
    def test_load_default_rules(self, engine):
        """Test loading default rules"""
        assert len(engine.rules) > 0
    
    def test_validate_package_name(self, engine):
        """Test package name validation"""
        violations = engine.validate("Create package neorl")
        assert len(violations) > 0
        assert any('package' in v['message'].lower() for v in violations)
    
    def test_validate_language(self, engine):
        """Test language validation"""
        violations = engine.validate("Write 中文 documentation")
        assert len(violations) > 0
        assert any('English' in v['message'] for v in violations)
    
    def test_validate_valid_text(self, engine):
        """Test valid text"""
        violations = engine.validate("claw-mem v1.0.3 release")
        assert len(violations) == 0
    
    def test_reload_config(self, engine, tmp_path):
        """Test config hot-reload"""
        # Reload should work without errors
        engine.config_path = str(tmp_path / "rules.json")
        engine.reload_config()
        assert len(engine.rules) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
