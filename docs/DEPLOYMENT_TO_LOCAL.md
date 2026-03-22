# claw-mem Local Deployment Guide

**Purpose:** Standardize the process of deploying new versions to local OpenClaw environment  
**Version:** v0.9.0+  
**Last Updated:** 2026-03-22

---

## 📋 Overview

After each GitHub release, deploy the new version to local OpenClaw environment to ensure you're always using the latest version.

---

## 🚀 Deployment Steps

### Step 1: Verify Release

Before deploying, confirm the release is complete:

```bash
# Check GitHub Release
gh release view v0.9.0 --repo opensourceclaw/claw-mem

# Or visit in browser
open https://github.com/opensourceclaw/claw-mem/releases/tag/v0.9.0
```

**Expected:** Release page shows all notes and assets

---

### Step 2: Pull Latest Code

```bash
cd /Users/liantian/workspace/osprojects/claw-mem
git checkout main
git pull origin main
git tag -l | grep v0.9  # Verify tag exists
```

**Expected Output:**
```
v0.9.0
```

---

### Step 3: Check Current Version

```bash
python3 -c "import claw_mem; print(f'Current version: {claw_mem.__version__}')"
```

**Expected:** Shows current installed version (e.g., `0.7.0` or `0.8.0`)

---

### Step 4: Uninstall Old Version

```bash
python3 -m pip uninstall claw-mem --break-system-packages -y
```

**Expected Output:**
```
Found existing installation: claw-mem 0.x.x
Uninstalling claw-mem-0.x.x:
  Successfully uninstalled claw-mem-0.x.x
```

---

### Step 5: Install New Version

```bash
cd /Users/liantian/workspace/osprojects/claw-mem
python3 -m pip install -e . --break-system-packages
```

**Expected Output:**
```
Obtaining file:///Users/liantian/workspace/osprojects/claw-mem
Installing collected packages: claw-mem
Successfully installed claw-mem-0.9.0
```

---

### Step 6: Verify Installation

```bash
python3 -c "
import claw_mem
from claw_mem import MemoryManager

print(f'✅ claw-mem version: {claw_mem.__version__}')
print(f'✅ MemoryManager available: {MemoryManager is not None}')
print(f'✅ Installation successful!')
"
```

**Expected Output:**
```
✅ claw-mem version: 0.9.0
✅ MemoryManager available: True
✅ Installation successful!
```

---

### Step 7: Test Basic Functionality

```bash
python3 -c "
from claw_mem import MemoryManager
import tempfile
import os

# Create temp workspace for testing
with tempfile.TemporaryDirectory() as tmpdir:
    # Initialize
    mem = MemoryManager(workspace=tmpdir)
    
    # Add a test memory
    mem.add('Test memory for v0.9.0 deployment')
    
    # Search
    results = mem.search('Test memory')
    
    print(f'✅ Added test memory')
    print(f'✅ Search returned {len(results)} results')
    print(f'✅ Basic functionality test passed!')
"
```

**Expected Output:**
```
✅ Added test memory
✅ Search returned 1 results
✅ Basic functionality test passed!
```

---

## 📝 Automation Script

Create a deployment script for future use:

```bash
#!/bin/bash
# deploy_to_local.sh - Deploy latest claw-mem to local OpenClaw

set -e

echo "🚀 Deploying claw-mem to local OpenClaw..."
echo "============================================"

# Check current version
echo "📋 Checking current version..."
CURRENT_VERSION=$(python3 -c "import claw_mem; print(claw_mem.__version__)" 2>/dev/null || echo "not installed")
echo "Current version: $CURRENT_VERSION"

# Uninstall old version
echo ""
echo "🗑️  Uninstalling old version..."
python3 -m pip uninstall claw-mem --break-system-packages -y || true

# Install new version
echo ""
echo "📦 Installing new version..."
cd /Users/liantian/workspace/osprojects/claw-mem
python3 -m pip install -e . --break-system-packages

# Verify installation
echo ""
echo "✅ Verifying installation..."
NEW_VERSION=$(python3 -c "import claw_mem; print(claw_mem.__version__)")
echo "New version: $NEW_VERSION"

# Test basic functionality
echo ""
echo "🧪 Testing basic functionality..."
python3 -c "
from claw_mem import MemoryManager
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    mem = MemoryManager(workspace=tmpdir)
    mem.add('Deployment test')
    results = mem.search('Deployment')
    print(f'Search test: {len(results)} results')
"

echo ""
echo "============================================"
echo "✅ Deployment complete! Version: $NEW_VERSION"
echo "============================================"
```

**Usage:**
```bash
chmod +x scripts/deploy_to_local.sh
./scripts/deploy_to_local.sh
```

---

## 🔄 Integration with Release Process

Add this step to the release checklist:

### Release Checklist (Updated)

```markdown
## Post-Release Deployment

- [ ] GitHub Release created
- [ ] Release notes published
- [ ] Git tag pushed
- [ ] **Deploy to local OpenClaw** ← NEW STEP
  - [ ] Uninstall old version
  - [ ] Install new version
  - [ ] Verify installation
  - [ ] Test basic functionality
- [ ] Update CHANGELOG.md
- [ ] Update documentation
```

---

## 🐛 Troubleshooting

### Issue: Uninstall fails

**Symptom:**
```
ERROR: Cannot uninstall claw-mem
```

**Solution:**
```bash
# Force uninstall
python3 -m pip uninstall claw-mem --break-system-packages --force-reinstall -y
```

---

### Issue: Import fails after install

**Symptom:**
```
ModuleNotFoundError: No module named 'claw_mem'
```

**Solution:**
```bash
# Reinstall with force
cd /Users/liantian/workspace/osprojects/claw-mem
python3 -m pip install -e . --break-system-packages --force-reinstall
```

---

### Issue: Version doesn't update

**Symptom:**
```
# Shows old version after install
python3 -c "import claw_mem; print(claw_mem.__version__)"
# Output: 0.8.0 (expected 0.9.0)
```

**Solution:**
```bash
# Clear Python cache
find ~/.cache/pip -name "*claw*" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Reinstall
python3 -m pip install -e . --break-system-packages --force-reinstall
```

---

### Issue: Permission denied

**Symptom:**
```
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied
```

**Solution:**
```bash
# Use --break-system-packages flag (already included in scripts)
python3 -m pip install -e . --break-system-packages

# Or use user installation
python3 -m pip install -e . --user
```

---

## 📊 Version History

| Date | Version | Deployed | Notes |
|------|---------|----------|-------|
| 2026-03-22 | v0.9.0 | ✅ Yes | 100% English documentation, performance improvements |
| 2026-03-21 | v0.8.0 | ❌ No | Skipped, deployed v0.9.0 directly |
| 2026-03-19 | v0.7.0 | ✅ Yes | Lazy loading, persistence, compression |

---

## ✅ Best Practices

1. **Always deploy after release** - Don't skip this step
2. **Test before using** - Run basic functionality test
3. **Keep script updated** - Update deploy script if process changes
4. **Document issues** - Add troubleshooting tips when encountered
5. **Backup config** - Backup config before major version upgrades

---

## 🔗 Related Documentation

- [Release Process](RELEASE_PROCESS.md) - How to create a release
- [CHANGELOG](../CHANGELOG.md) - Version history
- [Migration Guide](MIGRATION_GUIDE.md) - How to migrate between versions
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

---

*Document Created: 2026-03-22*  
*Version: v0.9.0*  
*claw-mem Project - Est. 2026*  
*"Ad Astra Per Aspera"*
