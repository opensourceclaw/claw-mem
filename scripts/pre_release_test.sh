#!/bin/bash
# Red Hat RHEL Style Pre-Release Test Script
# All tests must pass before release

set -e

echo "========================================"
echo "claw-mem v1.0.4 Pre-Release Tests"
echo "========================================"
echo ""

# Test 1: Integration Tests
echo "Test 1: Running integration tests..."
python3 tests/run_integration_tests.py
if [ $? -ne 0 ]; then
    echo "❌ Integration tests failed"
    exit 1
fi
echo "✅ Integration tests passed"
echo ""

# Test 2: Unit Tests
echo "Test 2: Running unit tests..."
python3 -m pytest tests/ -v --tb=short
if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed"
    exit 1
fi
echo "✅ Unit tests passed"
echo ""

# Test 3: Performance Tests
echo "Test 3: Running performance tests..."
python3 tests/test_performance.py
if [ $? -ne 0 ]; then
    echo "❌ Performance tests failed"
    exit 1
fi
echo "✅ Performance tests passed"
echo ""

# Test 4: Documentation Check
echo "Test 4: Checking documentation (100% English)..."
# Check for Chinese characters in docs
if grep -r "[\u4e00-\u9fff]" docs/*.md 2>/dev/null; then
    echo "❌ Chinese text found in documentation"
    exit 1
fi
echo "✅ Documentation is 100% English"
echo ""

# Test 5: Live Demo
echo "Test 5: Running live demo verification..."
python3 demo_v104_final.py
if [ $? -ne 0 ]; then
    echo "❌ Live demo failed"
    exit 1
fi
echo "✅ Live demo passed"
echo ""

echo "========================================"
echo "✅ ALL TESTS PASSED - Ready for Release!"
echo "========================================"
