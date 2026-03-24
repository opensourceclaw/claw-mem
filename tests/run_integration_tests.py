"""
Simple Integration Test Runner for v1.0.3

No pytest dependency - uses simple assertions.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path.home() / '.openclaw' / 'workspace' / 'skills' / 'claw-mem' / 'core'))

from semantic_detector import SemanticViolationDetector
from rule_engine import RuleEngine

def run_tests():
    """Run integration tests"""
    print("="*70)
    print("claw-mem v1.0.3 Integration Tests")
    print("="*70)
    print()
    
    passed = 0
    failed = 0
    
    # Test 1: Chinese detection
    print("Test 1: Chinese character detection")
    detector = SemanticViolationDetector()
    violations = detector.detect_violations("用中文写文档")
    if len(violations) > 0:
        print("  ✅ PASSED")
        passed += 1
    else:
        print("  ❌ FAILED")
        failed += 1
    
    # Test 2: Package name neorl
    print("Test 2: Package name 'neorl' detection")
    violations = detector.detect_violations("Create package neorl")
    if len(violations) > 0:
        print("  ✅ PASSED")
        passed += 1
    else:
        print("  ❌ FAILED")
        failed += 1
    
    # Test 3: Package name neomind
    print("Test 3: Package name 'neomind' detection")
    violations = detector.detect_violations("Import from neomind")
    if len(violations) > 0:
        print("  ✅ PASSED")
        passed += 1
    else:
        print("  ❌ FAILED")
        failed += 1
    
    # Test 4: Valid package name claw-mem
    print("Test 4: Valid package name 'claw-mem'")
    violations = detector.detect_violations("Use claw-mem package")
    if len(violations) == 0:
        print("  ✅ PASSED")
        passed += 1
    else:
        print("  ❌ FAILED")
        failed += 1
    
    # Test 5: Valid package name claw_rl
    print("Test 5: Valid package name 'claw_rl'")
    violations = detector.detect_violations("Use claw_rl package")
    if len(violations) == 0:
        print("  ✅ PASSED")
        passed += 1
    else:
        print("  ❌ FAILED")
        failed += 1
    
    # Test 6: Release title valid
    print("Test 6: Release title 'claw-mem v1.0.3'")
    is_valid, error = detector.validate_release_title("claw-mem v1.0.3")
    if is_valid:
        print("  ✅ PASSED")
        passed += 1
    else:
        print(f"  ❌ FAILED: {error}")
        failed += 1
    
    # Test 7: Release title valid with underscore
    print("Test 7: Release title 'claw_rl v1.0.3'")
    is_valid, error = detector.validate_release_title("claw_rl v1.0.3")
    if is_valid:
        print("  ✅ PASSED")
        passed += 1
    else:
        print(f"  ❌ FAILED: {error}")
        failed += 1
    
    # Test 8: Release title invalid with subtitle
    print("Test 8: Release title with subtitle (should fail)")
    is_valid, error = detector.validate_release_title("NeoMind v1.0.3 - Features")
    if not is_valid:
        print("  ✅ PASSED")
        passed += 1
    else:
        print("  ❌ FAILED")
        failed += 1
    
    # Test 9: Rule Engine loads config
    print("Test 9: Rule Engine loads configuration")
    engine = RuleEngine()
    if len(engine.rules) > 0:
        print(f"  ✅ PASSED ({len(engine.rules)} rules loaded)")
        passed += 1
    else:
        print("  ❌ FAILED")
        failed += 1
    
    # Test 10: Rule Engine detects violations
    print("Test 10: Rule Engine detects package name violation")
    violations = engine.validate("Create package neorl")
    if len(violations) > 0:
        print("  ✅ PASSED")
        passed += 1
    else:
        print("  ❌ FAILED")
        failed += 1
    
    # Test 11: Rule Engine detects language violation
    print("Test 11: Rule Engine detects language violation")
    violations = engine.validate("Write 中文 documentation")
    if len(violations) > 0:
        print("  ✅ PASSED")
        passed += 1
    else:
        print("  ❌ FAILED")
        failed += 1
    
    # Summary
    print()
    print("="*70)
    print(f"Test Summary: {passed} passed, {failed} failed")
    print(f"Success Rate: {passed/(passed+failed)*100:.1f}%")
    print("="*70)
    
    if failed == 0:
        print()
        print("✅ ALL TESTS PASSED - v1.0.3 is ready for release!")
        return True
    else:
        print()
        print("❌ SOME TESTS FAILED - Please fix before release!")
        return False


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
