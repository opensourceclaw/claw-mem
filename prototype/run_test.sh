#!/bin/bash
# Phase 0 Performance Test Runner
# 
# Usage: ./run_test.sh

set -e

echo "========================================"
echo "Phase 0: stdio JSON-RPC Performance Test"
echo "========================================"
echo ""

# Check Python
echo "[1/3] Checking Python..."
python3 --version

# Check Node.js
echo "[2/3] Checking Node.js..."
node --version

# Check TypeScript
echo "[3/3] Checking TypeScript..."
if ! command -v ts-node &> /dev/null; then
    echo "Installing ts-node..."
    npm install -g ts-node typescript
fi
ts-node --version

echo ""
echo "Starting tests..."
echo ""

# Run test
ts-node prototype/bridge_client_prototype.ts

echo ""
echo "Test completed!"
