#!/bin/bash
# deploy_to_local.sh - Deploy latest claw-mem to local OpenClaw
# Usage: ./scripts/deploy_to_local.sh [version]
# Example: ./scripts/deploy_to_local.sh v0.9.0

set -e

echo "🚀 Deploying claw-mem to local OpenClaw..."
echo "============================================"

# Get version from argument or auto-detect
VERSION=${1:-""}

if [ -z "$VERSION" ]; then
    # Auto-detect from git tag
    VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "unknown")
    echo "📋 Auto-detected version: $VERSION"
else
    echo "📋 Target version: $VERSION"
fi

# Check current version
echo ""
echo "📋 Checking current version..."
CURRENT_VERSION=$(python3 -c "import claw_mem; print(claw_mem.__version__)" 2>/dev/null || echo "not installed")
echo "Current version: $CURRENT_VERSION"

if [ "$CURRENT_VERSION" == "$VERSION" ]; then
    echo "⚠️  Version $VERSION is already installed"
    read -p "Continue with reinstallation? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelled"
        exit 0
    fi
fi

# Uninstall old version
echo ""
echo "🗑️  Uninstalling old version..."
python3 -m pip uninstall claw-mem --break-system-packages -y || true

# Install new version
echo ""
echo "📦 Installing new version..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( dirname "$SCRIPT_DIR" )"
cd "$PROJECT_DIR"

python3 -m pip install -e . --break-system-packages

# Verify installation
echo ""
echo "✅ Verifying installation..."
NEW_VERSION=$(python3 -c "import claw_mem; print(claw_mem.__version__)")
echo "New version: $NEW_VERSION"

if [ "$NEW_VERSION" != "$VERSION" ] && [ "$VERSION" != "unknown" ]; then
    echo "⚠️  Warning: Expected version $VERSION, got $NEW_VERSION"
fi

# Test basic functionality
echo ""
echo "🧪 Testing basic functionality..."
python3 -c "
from claw_mem import MemoryManager
import tempfile
import sys

try:
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = MemoryManager(workspace=tmpdir)
        
        # Store test memory
        mem.store('Deployment test for version $VERSION')
        
        # Search
        results = mem.search('Deployment test')
        
        if len(results) > 0:
            print(f'✅ Search test: {len(results)} results')
            print('✅ Basic functionality test passed!')
            sys.exit(0)
        else:
            print('❌ Search returned no results')
            sys.exit(1)
except Exception as e:
    print(f'❌ Test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

TEST_RESULT=$?

echo ""
echo "============================================"
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ Deployment complete! Version: $NEW_VERSION"
    echo "============================================"
    exit 0
else
    echo "❌ Deployment completed with errors"
    echo "============================================"
    exit 1
fi
