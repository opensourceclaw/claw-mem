#!/bin/bash
# claw-mem Upgrade Script v0.5.0 → v0.6.0
# 
# Features:
# - Mandatory backup before upgrade
# - Automatic uninstall of v0.5.0
# - Memory files preservation
# - Installation of v0.6.0
# - Post-upgrade verification
#
# Usage: ./upgrade_to_v060.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Workspace paths
WORKSPACE_DIR="$HOME/.openclaw/workspace"
BACKUP_DIR="$HOME/claw-mem-backup-$(date +%Y%m%d-%H%M%S)"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   claw-mem Upgrade Script: v0.5.0 → v0.6.0            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function: Print status
print_status() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Verify prerequisites
print_status "Step 1/7: Verifying prerequisites..."

if ! command -v python &> /dev/null; then
    print_error "Python not found. Please install Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
print_success "Python version: $PYTHON_VERSION"

if ! command -v pip &> /dev/null; then
    print_error "pip not found. Please install pip"
    exit 1
fi

print_success "Prerequisites verified"
echo ""

# Step 2: Create mandatory backup
print_status "Step 2/7: Creating mandatory backup..."
print_warning "Backup location: $BACKUP_DIR"

mkdir -p "$BACKUP_DIR"

# Backup MEMORY.md
if [ -f "$WORKSPACE_DIR/MEMORY.md" ]; then
    cp "$WORKSPACE_DIR/MEMORY.md" "$BACKUP_DIR/"
    print_success "Backed up MEMORY.md"
else
    print_warning "MEMORY.md not found (fresh install?)"
fi

# Backup memory/ directory
if [ -d "$WORKSPACE_DIR/memory" ]; then
    cp -r "$WORKSPACE_DIR/memory" "$BACKUP_DIR/"
    print_success "Backed up memory/ directory"
else
    print_warning "memory/ directory not found (fresh install?)"
fi

# Count backed up files
BACKUP_FILES=$(find "$BACKUP_DIR" -type f | wc -l)
print_success "Backup created: $BACKUP_FILES files"
echo ""

# Step 3: Uninstall v0.5.0
print_status "Step 3/7: Uninstalling v0.5.0..."

if pip show claw-mem &> /dev/null; then
    CURRENT_VERSION=$(pip show claw-mem | grep Version | awk '{print $2}')
    print_warning "Current version: $CURRENT_VERSION"
    
    pip uninstall claw-mem -y
    print_success "v0.5.0 uninstalled"
else
    print_warning "claw-mem not installed (fresh install?)"
fi
echo ""

# Step 4: Verify memory files intact
print_status "Step 4/7: Verifying memory files integrity..."

MEMORY_INTACT=true

if [ -f "$WORKSPACE_DIR/MEMORY.md" ]; then
    print_success "MEMORY.md preserved"
else
    print_error "MEMORY.md missing!"
    MEMORY_INTACT=false
fi

if [ -d "$WORKSPACE_DIR/memory" ]; then
    MEMORY_FILES=$(find "$WORKSPACE_DIR/memory" -name "*.md" | wc -l)
    print_success "memory/ directory preserved ($MEMORY_FILES files)"
else
    print_error "memory/ directory missing!"
    MEMORY_INTACT=false
fi

if [ "$MEMORY_INTACT" = false ]; then
    print_error "Memory files integrity check failed!"
    print_warning "Backup location: $BACKUP_DIR"
    exit 1
fi
echo ""

# Step 5: Install v0.6.0
print_status "Step 5/7: Installing v0.6.0..."

# Check if running from claw-mem directory (development installation)
if [ -f "pyproject.toml" ]; then
    print_warning "Installing from local source (development mode)..."
    pip install -e . jieba
else
    print_warning "Installing from PyPI..."
    pip install claw-mem jieba
fi

print_success "v0.6.0 installed"
echo ""

# Step 6: Verify installation
print_status "Step 6/7: Verifying installation..."

if python -c "from claw_mem import MemoryManager" 2>/dev/null; then
    print_success "Import test passed"
else
    print_error "Import test failed!"
    print_warning "Rollback may be required"
    print_warning "Backup location: $BACKUP_DIR"
    exit 1
fi
echo ""

# Step 7: Test memory continuity
print_status "Step 7/7: Testing memory continuity..."

python << 'PYTHON_SCRIPT'
from claw_mem import MemoryManager
from pathlib import Path

try:
    workspace = Path.home() / '.openclaw' / 'workspace'
    mm = MemoryManager(workspace=str(workspace))
    mm.start_session('upgrade_verification')
    
    stats = mm.get_stats()
    memory_count = stats['working_memory_count']
    
    if memory_count > 0:
        print(f"SUCCESS: Loaded {memory_count} memories from v0.5.0")
    else:
        print("WARNING: No memories loaded (may be fresh install)")
    
    # Test search
    results = mm.search("test", limit=5)
    print(f"SUCCESS: Search working ({len(results)} results)")
    
    mm.end_session()
    print("SUCCESS: Memory continuity verified")
    
except Exception as e:
    print(f"ERROR: Memory continuity test failed: {e}")
    exit(1)
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    print_success "Memory continuity verified"
else
    print_error "Memory continuity test failed!"
    print_warning "Rollback may be required"
    print_warning "Backup location: $BACKUP_DIR"
    exit 1
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ Upgrade completed successfully!                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Backup location:${NC} $BACKUP_DIR"
echo -e "${BLUE}To cleanup backup (after verification):${NC}"
echo -e "  ${YELLOW}rm -rf $BACKUP_DIR${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Test claw-mem in your application"
echo "  2. Verify all features working"
echo "  3. Cleanup backup when confident"
echo ""
