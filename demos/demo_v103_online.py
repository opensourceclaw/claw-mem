"""
claw-mem v1.0.3 Live Demo - Online Verification

This demo proves v1.0.3 is deployed and running:
1. Semantic Violation Detector
2. Configurable Rule Engine
3. Package Name Validation
4. Release Title Format Enforcement
"""

from pathlib import Path
import sys

# Use deployed v1.0.3 from system
sys.path.insert(0, str(Path.home() / '.openclaw' / 'workspace' / 'skills' / 'claw-mem' / 'core'))

from semantic_detector import SemanticViolationDetector
from rule_engine import RuleEngine


def run_demo():
    """Run live v1.0.3 verification demo"""
    
    print("="*70)
    print("claw-mem v1.0.3 LIVE ONLINE VERIFICATION")
    print("="*70)
    print()
    
    # Initialize v1.0.3 components
    detector = SemanticViolationDetector()
    engine = RuleEngine()
    
    print("✅ v1.0.3 Components initialized from deployed location")
    print(f"   Location: ~/.openclaw/workspace/skills/claw-mem/core/")
    print()
    
    # ================================================================
    # Test 1: Semantic Violation Detector
    # ================================================================
    print("="*70)
    print("Test 1: Semantic Violation Detector")
    print("="*70)
    print()
    
    test_cases = [
        ("Write English docs", False, "English content"),
        ("用中文写文档", True, "Chinese content"),
        ("Create package claw_rl", False, "Valid package name"),
        ("Create package neorl", True, "Invalid package name"),
        ("Import from neomind", True, "Invalid package alias"),
    ]
    
    passed = 0
    for text, should_violate, description in test_cases:
        violations = detector.detect_violations(text)
        has_violation = len(violations) > 0
        status = '✅' if has_violation == should_violate else '❌'
        
        if has_violation == should_violate:
            passed += 1
        
        print(f"  {status} {description}")
        print(f"     Text: {text}")
        print(f"     Expected violation: {should_violate}, Got: {has_violation}")
        if has_violation:
            for v in violations:
                print(f"     - {v.message}")
        print()
    
    print(f"Test 1 Result: {passed}/{len(test_cases)} passed")
    print()
    
    # ================================================================
    # Test 2: Release Title Validation
    # ================================================================
    print("="*70)
    print("Test 2: Release Title Format Enforcement")
    print("="*70)
    print()
    
    title_tests = [
        ("claw-mem v1.0.3", True, "Valid format"),
        ("claw_rl v1.0.3", True, "Valid format"),
        ("NeoMind v1.0.3 - Cool Features", False, "Has subtitle"),
        ("Release v1.0.3: Update", False, "Has colon"),
        ("Version 1.0.3", False, "Wrong format"),
    ]
    
    passed = 0
    for title, should_be_valid, description in title_tests:
        is_valid, error = detector.validate_release_title(title)
        status = '✅' if is_valid == should_be_valid else '❌'
        
        if is_valid == should_be_valid:
            passed += 1
        
        print(f"  {status} {description}")
        print(f"     Title: {title}")
        print(f"     Expected valid: {should_be_valid}, Got: {is_valid}")
        if not is_valid and error:
            print(f"     Error: {error}")
        print()
    
    print(f"Test 2 Result: {passed}/{len(title_tests)} passed")
    print()
    
    # ================================================================
    # Test 3: Configurable Rule Engine
    # ================================================================
    print("="*70)
    print("Test 3: Configurable Rule Engine")
    print("="*70)
    print()
    
    print(f"  Loaded {len(engine.rules)} rules from configuration")
    for i, rule in enumerate(engine.rules, 1):
        print(f"    {i}. {rule.name} ({rule.type})")
    print()
    
    rule_tests = [
        ("Create package neorl", True, "Package name violation"),
        ("Write 中文 documentation", True, "Language violation"),
        ("claw-mem v1.0.3 release", False, "Valid text"),
    ]
    
    passed = 0
    for text, should_violate, description in rule_tests:
        violations = engine.validate(text)
        has_violation = len(violations) > 0
        status = '✅' if has_violation == should_violate else '❌'
        
        if has_violation == should_violate:
            passed += 1
        
        print(f"  {status} {description}")
        print(f"     Text: {text}")
        print(f"     Expected violation: {should_violate}, Got: {has_violation}")
        if has_violation:
            for v in violations:
                print(f"     - [{v['severity']}] {v['message']}")
        print()
    
    print(f"Test 3 Result: {passed}/{len(rule_tests)} passed")
    print()
    
    # ================================================================
    # SUMMARY
    # ================================================================
    print("="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    print()
    
    total_tests = len(test_cases) + len(title_tests) + len(rule_tests)
    total_passed = sum([
        sum(1 for t in test_cases if detector.detect_violations(t[0]) != [] == t[1]),
        sum(1 for t in title_tests if detector.validate_release_title(t[0])[0] == t[1]),
        sum(1 for t in rule_tests if engine.validate(t[0]) != [] == t[1])
    ])
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_tests - total_passed}")
    print(f"Success Rate: {total_passed/total_tests*100:.1f}%")
    print()
    
    if total_passed == total_tests:
        print("="*70)
        print("✅ claw-mem v1.0.3 VERIFICATION COMPLETE - ALL TESTS PASSED!")
        print("="*70)
        print()
        print("v1.0.3 is ONLINE and RUNNING!")
        print("Location: ~/.openclaw/workspace/skills/claw-mem/")
    else:
        print("="*70)
        print("⚠️ Some tests failed. Please check deployment.")
        print("="*70)


if __name__ == '__main__':
    run_demo()
