"""
claw-mem v1.0.4 Final Verification

Red Hat RHEL Style Release Verification
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path.home() / '.openclaw' / 'workspace' / 'skills' / 'claw-mem' / 'core'))

from semantic_detector import SemanticViolationDetector
from rule_engine import RuleEngine

def run_final_verification():
    """Run final verification"""
    
    print("="*70)
    print("claw-mem v1.0.4 FINAL VERIFICATION")
    print("="*70)
    print()
    
    detector = SemanticViolationDetector()
    engine = RuleEngine()
    
    all_passed = True
    
    # Test 1: Chinese detection
    print("Test 1: Chinese Character Detection")
    violations = detector.detect_violations("用中文写文档")
    if len(violations) > 0:
        print("  ✅ PASSED")
    else:
        print("  ❌ FAILED")
        all_passed = False
    
    # Test 2: Package name validation
    print("Test 2: Package Name Validation")
    tests = [
        ("neorl", True),
        ("neomind", True),
        ("claw_rl", False),
        ("claw-mem", False),
    ]
    for name, should_violate in tests:
        violations = detector.detect_violations(f"Create package {name}")
        has_violation = len(violations) > 0
        if has_violation == should_violate:
            print(f"  ✅ {name}: {'Correctly rejected' if should_violate else 'Correctly accepted'}")
        else:
            print(f"  ❌ {name}: {'Should reject' if should_violate else 'Should accept'}")
            all_passed = False
    
    # Test 3: Release title validation
    print("Test 3: Release Title Validation")
    tests = [
        ("claw-mem v1.0.4", True),
        ("claw_rl v1.0.4", True),
        ("NeoMind v1.0.4 - Features", False),
    ]
    for title, should_valid in tests:
        is_valid, error = detector.validate_release_title(title)
        if is_valid == should_valid:
            print(f"  ✅ '{title}': {'Valid' if should_valid else 'Invalid'}")
        else:
            print(f"  ❌ '{title}': {'Should be valid' if should_valid else 'Should be invalid'}")
            all_passed = False
    
    # Test 4: Rule Engine
    print("Test 4: Rule Engine")
    print(f"  Loaded {len(engine.rules)} rules")
    violations = engine.validate("Create package neorl")
    if len(violations) > 0:
        print("  ✅ PASSED")
    else:
        print("  ❌ FAILED")
        all_passed = False
    
    # Test 5: Performance
    print("Test 5: Performance")
    import time
    start = time.perf_counter()
    for _ in range(100):
        detector.detect_violations("Create package neorl")
    end = time.perf_counter()
    avg_latency_ms = (end - start) / 100 * 1000
    print(f"  Average latency: {avg_latency_ms:.2f}ms")
    if avg_latency_ms < 50:
        print("  ✅ PASSED (<50ms)")
    else:
        print("  ❌ FAILED (>50ms)")
        all_passed = False
    
    # Summary
    print()
    print("="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED - v1.0.4 READY FOR RELEASE!")
    else:
        print("❌ SOME TESTS FAILED - Please fix before release!")
    print("="*70)
    
    return all_passed

if __name__ == '__main__':
    success = run_final_verification()
    sys.exit(0 if success else 1)
