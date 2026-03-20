# claw-mem Installation and Deployment Guide

**Version**: 0.6.0  
**Last Updated**: 2026-03-18  
**Status**: Draft (Pending Review)

---

## Overview

This guide covers installation, upgrade, and deployment procedures for claw-mem v0.6.0, ensuring data persistence and memory continuity.

---

## System Requirements

### Minimum Requirements

- **Python**: 3.9+
- **Memory**: 100MB RAM
- **Disk**: 50MB free space
- **OS**: macOS/Linux/Windows

### Recommended Requirements

- **Python**: 3.10+
- **Memory**: 200MB RAM
- **Disk**: 100MB free space
- **OS**: macOS 12+/Ubuntu 20.04+/Windows 11

---

## Installation Scenarios

### Scenario 1: Fresh Installation

For users installing claw-mem for the first time.

### Scenario 2: Upgrade from v0.5.0 to v0.6.0

For existing users upgrading while preserving memory data.

### Scenario 3: Development Installation

For contributors and developers.

---

## Scenario 1: Fresh Installation

### Step 1: Verify Prerequisites

```bash
# Check Python version
python --version
# Expected: Python 3.9+

# Check pip version
pip --version
# Expected: pip 21.0+
```

### Step 2: Install claw-mem

```bash
# Standard installation
pip install claw-mem

# With Chinese support (recommended)
pip install claw-mem jieba
```

### Step 3: Verify Installation

```bash
# Test import
python -c "from claw_mem import MemoryManager; print('✅ Installation successful')"
```

### Step 4: Initialize Workspace (Optional)

```bash
# Default workspace location
# macOS/Linux: ~/.openclaw/workspace
# Windows: %USERPROFILE%\.openclaw\workspace

# No manual initialization needed - claw-mem auto-creates structure
```

---

## Scenario 2: Upgrade from v0.5.0 to v0.6.0

### ⚠️ Critical: Preserve Memory Data

**Memory files location**: `~/.openclaw/workspace/`

**Files to preserve**:
- `MEMORY.md` (Semantic memory)
- `memory/YYYY-MM-DD.md` (Episodic memory)
- `memory/skills/*.md` (Procedural memory)

### Step 1: Backup Memory Data (Recommended)

```bash
# Create backup directory
BACKUP_DIR=~/claw-mem-backup-$(date +%Y%m%d-%H%M%S)
mkdir -p $BACKUP_DIR

# Backup memory files
cp -r ~/.openclaw/workspace/MEMORY.md $BACKUP_DIR/
cp -r ~/.openclaw/workspace/memory/ $BACKUP_DIR/

echo "✅ Backup created: $BACKUP_DIR"
```

### Step 2: Uninstall v0.5.0

```bash
# Uninstall old version
pip uninstall claw-mem -y

# Verify uninstallation
python -c "import claw_mem" 2>&1 || echo "✅ v0.5.0 uninstalled"
```

### Step 3: Verify Memory Files Intact

```bash
# Check memory files still exist
ls -la ~/.openclaw/workspace/MEMORY.md
ls -la ~/.openclaw/workspace/memory/

# Expected: Files should still be present
```

### Step 4: Install v0.6.0

```bash
# Install new version
pip install claw-mem jieba

# Verify installation
python -c "from claw_mem import MemoryManager; print('✅ v0.6.0 installed')"
```

### Step 5: Verify Memory Continuity

```python
from claw_mem import MemoryManager
from pathlib import Path

# Initialize with existing workspace
workspace = Path.home() / '.openclaw' / 'workspace'
mm = MemoryManager(workspace=str(workspace))

# Start session (auto-loads existing memories)
mm.start_session('upgrade_test')

# Verify memories loaded
stats = mm.get_stats()
print(f"✅ Loaded {stats['working_memory_count']} memories from v0.5.0")

# Test search
results = mm.search("test", limit=5)
print(f"✅ Search working: {len(results)} results")

mm.end_session()
```

### Step 6: Cleanup (Optional)

```bash
# Remove backup after successful verification
# rm -rf ~/claw-mem-backup-*
```

---

## Scenario 3: Development Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/opensourceclaw/claw-mem/claw-mem.git
cd claw-mem
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### Step 3: Install Development Dependencies

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
python -m pytest tests/ -v
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Verify system requirements met
- [ ] Backup existing memory data (if upgrading)
- [ ] Document current version

### Installation

- [ ] Uninstall old version (if upgrading)
- [ ] Verify memory files intact
- [ ] Install new version
- [ ] Verify installation

### Post-Deployment

- [ ] Test import
- [ ] Verify memory continuity
- [ ] Test search functionality
- [ ] Document deployment success

---

## Troubleshooting

### Issue 1: Import Error After Upgrade

**Symptom**: `ModuleNotFoundError: No module named 'claw_mem'`

**Solution**:
```bash
# Verify pip installation path
pip show claw-mem

# Reinstall if necessary
pip uninstall claw-mem -y
pip install claw-mem --force-reinstall
```

### Issue 2: Memory Files Not Found

**Symptom**: `FileNotFoundError: [Errno 2] No such file or directory`

**Solution**:
```bash
# Check workspace location
ls -la ~/.openclaw/workspace/

# Restore from backup if needed
cp ~/claw-mem-backup-*/MEMORY.md ~/.openclaw/workspace/
cp -r ~/claw-mem-backup-*/memory/ ~/.openclaw/workspace/
```

### Issue 3: Jieba Not Found

**Symptom**: `ImportError: No module named 'jieba'`

**Solution**:
```bash
# Install Jieba
pip install jieba

# Or install with Chinese support
pip install claw-mem[chinese]
```

### Issue 4: Index Build Slow

**Symptom**: Session startup takes >2 seconds

**Solution**:
```python
# This is normal for first startup (index build)
# Subsequent sessions will be faster after index persistence (v0.7.0)

# Workaround: Reduce memory count
# - Archive old episodic memories
# - Keep only recent 30 days
```

---

## Migration Script (Automated Upgrade)

For users who prefer automated upgrade:

```bash
#!/bin/bash
# upgrade_to_v060.sh

set -e

echo "🚀 claw-mem Upgrade to v0.6.0"
echo "=============================="

# Step 1: Backup
BACKUP_DIR=~/claw-mem-backup-$(date +%Y%m%d-%H%M%S)
echo "📦 Creating backup: $BACKUP_DIR"
mkdir -p $BACKUP_DIR
cp -r ~/.openclaw/workspace/MEMORY.md $BACKUP_DIR/ 2>/dev/null || true
cp -r ~/.openclaw/workspace/memory/ $BACKUP_DIR/ 2>/dev/null || true
echo "✅ Backup created"

# Step 2: Uninstall old version
echo "🗑️  Uninstalling old version..."
pip uninstall claw-mem -y || true
echo "✅ Old version uninstalled"

# Step 3: Verify memory files
echo "🔍 Verifying memory files..."
if [ -f ~/.openclaw/workspace/MEMORY.md ]; then
    echo "✅ MEMORY.md preserved"
else
    echo "⚠️  MEMORY.md not found (fresh install?)"
fi

# Step 4: Install new version
echo "📦 Installing v0.6.0..."
pip install claw-mem jieba
echo "✅ v0.6.0 installed"

# Step 5: Verify installation
echo "🔍 Verifying installation..."
python -c "from claw_mem import MemoryManager; print('✅ Installation verified')"

# Step 6: Test memory continuity
echo "🧪 Testing memory continuity..."
python -c "
from claw_mem import MemoryManager
from pathlib import Path
mm = MemoryManager(workspace=str(Path.home() / '.openclaw' / 'workspace'))
mm.start_session('upgrade_verification')
stats = mm.get_stats()
print(f'✅ Loaded {stats[\"working_memory_count\"]} memories')
mm.end_session()
"

echo ""
echo "🎉 Upgrade completed successfully!"
echo "Backup location: $BACKUP_DIR"
echo ""
echo "To cleanup backup (after verification):"
echo "  rm -rf $BACKUP_DIR"
```

### Usage

```bash
# Make script executable
chmod +x upgrade_to_v060.sh

# Run upgrade
./upgrade_to_v060.sh
```

---

## Rollback Procedure

If upgrade fails, rollback to v0.5.0:

### Step 1: Uninstall v0.6.0

```bash
pip uninstall claw-mem -y
```

### Step 2: Restore from Backup

```bash
BACKUP_DIR=~/claw-mem-backup-YYYYMMDD-HHMMSS

# Restore memory files
cp $BACKUP_DIR/MEMORY.md ~/.openclaw/workspace/
cp -r $BACKUP_DIR/memory/ ~/.openclaw/workspace/
```

### Step 3: Reinstall v0.5.0

```bash
pip install claw-mem==0.5.0
```

### Step 4: Verify Rollback

```bash
python -c "
from claw_mem import MemoryManager
mm = MemoryManager()
mm.start_session('rollback_test')
print('✅ Rollback successful')
mm.end_session()
"
```

---

## Best Practices

### 1. Always Backup Before Upgrade

```bash
# Create timestamped backup
BACKUP_DIR=~/claw-mem-backup-$(date +%Y%m%d-%H%M%S)
mkdir -p $BACKUP_DIR
cp -r ~/.openclaw/workspace/MEMORY.md $BACKUP_DIR/
cp -r ~/.openclaw/workspace/memory/ $BACKUP_DIR/
```

### 2. Test in Staging Environment

```bash
# Create test workspace
mkdir -p /tmp/claw-mem-test
cp -r ~/.openclaw/workspace/MEMORY.md /tmp/claw-mem-test/
cp -r ~/.openclaw/workspace/memory/ /tmp/claw-mem-test/

# Test upgrade with test workspace
python -c "
from claw_mem import MemoryManager
mm = MemoryManager(workspace='/tmp/claw-mem-test')
mm.start_session('test')
print('✅ Test passed')
mm.end_session()
"
```

### 3. Document Upgrade Process

```bash
# Keep upgrade log
cat >> ~/claw-mem-upgrade.log << EOF
Date: $(date)
From: v0.5.0
To: v0.6.0
Backup: $BACKUP_DIR
Status: SUCCESS
EOF
```

---

## Support

- **Documentation**: https://github.com/opensourceclaw/claw-mem/tree/main/docs
- **Issues**: https://github.com/opensourceclaw/claw-mem/issues
- **Discussions**: https://github.com/opensourceclaw/claw-mem/discussions

---

**End of Deployment Guide**
