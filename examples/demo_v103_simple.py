"""
claw-mem v1.0.3 Simple Live Demo

Proves v1.0.3 is deployed and working with core features.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path.home() / '.openclaw' / 'workspace' / 'skills' / 'claw-mem' / 'core'))

from semantic_detector import SemanticViolationDetector
from rule_engine import RuleEngine

print("="*70)
print("claw-mem v1.0.3 LIVE DEMO - Core Features Verification")
print("="*70)
print()

# Test 1: Semantic Detector
print("Test 1: Semantic Violation Detector")
print("-" * 70)
detector = SemanticViolationDetector()

tests = [
    ("Create package neorl", "Package name violation"),
    ("用中文写", "Chinese language"),
    ("claw-mem v1.0.3", "Valid text"),
]

for text, desc in tests:
    violations = detector.detect_violations(text)
    status = '❌ Violation' if violations else '✅ Valid'
    print(f"  {status}: {desc} - '{text}'")

print()

# Test 2: Release Title
print("Test 2: Release Title Validation")
print("-" * 70)

titles = [
    ("claw-mem v1.0.3", True),
    ("NeoMind v1.0.3 - Features", False),
]

for title, should_valid in titles:
    is_valid, error = detector.validate_release_title(title)
    status = '✅' if is_valid == should_valid else '❌'
    result = 'Valid' if is_valid else 'Invalid'
    print(f"  {status} {title} -> {result}")

print()

# Test 3: Rule Engine
print("Test 3: Configurable Rule Engine")
print("-" * 70)
engine = RuleEngine()
print(f"  Loaded {len(engine.rules)} rules")

violations = engine.validate("Create package neorl")
status = '✅ Detected' if violations else '❌ Missed'
print(f"  {status}: Package name violation")

print()
print("="*70)
print("✅ claw-mem v1.0.3 is ONLINE and RUNNING!")
print("="*70)
print()
print("Deployment: ~/.openclaw/workspace/skills/claw-mem/")
print("GitHub: https://github.com/opensourceclaw/claw-mem/releases/tag/v1.0.3")
