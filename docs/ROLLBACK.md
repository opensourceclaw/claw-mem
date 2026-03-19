# claw-mem Rollback Procedure

**Version**: 0.6.0 → 0.5.0  
**Last Updated**: 2026-03-18  
**Status**: Ready for Emergency Use

---

## When to Rollback

Rollback from v0.6.0 to v0.5.0 may be necessary if:

- ❌ Critical bugs discovered in v0.6.0
- ❌ Memory data corruption detected
- ❌ Performance degradation unacceptable
- ❌ Compatibility issues with existing workflows
- ❌ Upgrade verification failed

---

## Rollback Scenarios

### Scenario 1: Immediate Rollback (Upgrade Failed)

**Trigger**: Upgrade script failed or verification failed

**Action**: Execute rollback immediately

### Scenario 2: Delayed Rollback (Issues Discovered Later)

**Trigger**: Issues discovered after successful upgrade

**Action**: Execute rollback after documenting issues

---

## Prerequisites

Before rollback, ensure you have:

- ✅ Backup directory from upgrade (e.g., `~/claw-mem-backup-20260318-140000`)
- ✅ Internet connection (for pip install)
- ✅ Python 3.9+ available
- ✅ pip available

**If backup is missing**:
```bash
# Create backup before rollback
BACKUP_DIR=~/claw-mem-rollback-backup-$(date +%Y%m%d-%H%M%S)
mkdir -p $BACKUP_DIR
cp -r ~/.openclaw/workspace/MEMORY.md $BACKUP_DIR/ 2>/dev/null || true
cp -r ~/.openclaw/workspace/memory/ $BACKUP_DIR/ 2>/dev/null || true
echo "Emergency backup created: $BACKUP_DIR"
```

---

## Rollback Procedure

### Step 1: Document Current State

```bash
# Record current version
pip show claw-mem | grep Version

# Record current issues
cat > ~/claw-mem-rollback-reason.txt << EOF
Date: $(date)
From Version: v0.6.0
To Version: v0.5.0
Reason: [Describe the issue]
Backup Location: [Backup directory]
EOF
```

### Step 2: Backup Current State (Optional but Recommended)

```bash
# Create backup of current state
ROLLBACK_BACKUP=~/claw-mem-v060-backup-$(date +%Y%m%d-%H%M%S)
mkdir -p $ROLLBACK_BACKUP

cp -r ~/.openclaw/workspace/MEMORY.md $ROLLBACK_BACKUP/ 2>/dev/null || true
cp -r ~/.openclaw/workspace/memory/ $ROLLBACK_BACKUP/ 2>/dev/null || true

echo "Current state backup: $ROLLBACK_BACKUP"
```

### Step 3: Uninstall v0.6.0

```bash
# Uninstall v0.6.0
pip uninstall claw-mem -y

# Verify uninstallation
python -c "import claw_mem" 2>&1 || echo "✅ v0.6.0 uninstalled"
```

### Step 4: Restore Memory Files from Original Backup

```bash
# Find original backup directory
# Format: ~/claw-mem-backup-YYYYMMDD-HHMMSS

# List available backups
ls -d ~/claw-mem-backup-* 2>/dev/null || echo "No backups found"

# Restore from backup (replace with actual backup directory)
ORIGINAL_BACKUP=~/claw-mem-backup-20260318-140000  # UPDATE THIS

if [ -d "$ORIGINAL_BACKUP" ]; then
    # Restore MEMORY.md
    if [ -f "$ORIGINAL_BACKUP/MEMORY.md" ]; then
        cp "$ORIGINAL_BACKUP/MEMORY.md" ~/.openclaw/workspace/
        echo "✅ MEMORY.md restored"
    fi
    
    # Restore memory/ directory
    if [ -d "$ORIGINAL_BACKUP/memory" ]; then
        rm -rf ~/.openclaw/workspace/memory
        cp -r "$ORIGINAL_BACKUP/memory" ~/.openclaw/workspace/
        echo "✅ memory/ directory restored"
    fi
else
    echo "❌ Backup directory not found: $ORIGINAL_BACKUP"
    echo "Please update ORIGINAL_BACKUP variable with correct path"
    exit 1
fi
```

### Step 5: Install v0.5.0

```bash
# Install v0.5.0
pip install claw-mem==0.5.0

# Verify installation
python -c "from claw_mem import MemoryManager; print('✅ v0.5.0 installed')"
```

### Step 6: Verify Rollback

```bash
python << 'PYTHON_SCRIPT'
from claw_mem import MemoryManager
from pathlib import Path

try:
    workspace = Path.home() / '.openclaw' / 'workspace'
    mm = MemoryManager(workspace=str(workspace))
    mm.start_session('rollback_verification')
    
    stats = mm.get_stats()
    memory_count = stats['working_memory_count']
    
    print(f"✅ Loaded {memory_count} memories")
    
    if memory_count > 0:
        print("✅ Memory continuity verified")
    else:
        print("⚠️  No memories loaded (check memory files)")
    
    # Test search
    results = mm.search("test", limit=5)
    print(f"✅ Search working ({len(results)} results)")
    
    mm.end_session()
    print("✅ Rollback verification completed")
    
except Exception as e:
    print(f"❌ Rollback verification failed: {e}")
    exit(1)
PYTHON_SCRIPT
```

### Step 7: Document Rollback Completion

```bash
cat >> ~/claw-mem-rollback-reason.txt << EOF

Rollback Completed: $(date)
Status: SUCCESS
Memory Files: RESTORED
Backup Used: $ORIGINAL_BACKUP
EOF

echo "Rollback documented in: ~/claw-mem-rollback-reason.txt"
```

---

## Automated Rollback Script

For emergency situations, use automated rollback:

```bash
#!/bin/bash
# rollback_to_v050.sh
# 
# WARNING: This script will rollback claw-mem from v0.6.0 to v0.5.0
# Only use if you have a backup from the upgrade process.

set -e

echo "⚠️  WARNING: This will rollback claw-mem from v0.6.0 to v0.5.0"
echo ""
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

# Find most recent backup
LATEST_BACKUP=$(ls -td ~/claw-mem-backup-* 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ No backup found. Cannot proceed with rollback."
    echo "Please create a backup manually first."
    exit 1
fi

echo "Using backup: $LATEST_BACKUP"
echo ""

# Step 1: Uninstall v0.6.0
echo "Uninstalling v0.6.0..."
pip uninstall claw-mem -y

# Step 2: Restore memory files
echo "Restoring memory files..."
if [ -f "$LATEST_BACKUP/MEMORY.md" ]; then
    cp "$LATEST_BACKUP/MEMORY.md" ~/.openclaw/workspace/
    echo "✅ MEMORY.md restored"
fi

if [ -d "$LATEST_BACKUP/memory" ]; then
    rm -rf ~/.openclaw/workspace/memory
    cp -r "$LATEST_BACKUP/memory" ~/.openclaw/workspace/
    echo "✅ memory/ restored"
fi

# Step 3: Install v0.5.0
echo "Installing v0.5.0..."
pip install claw-mem==0.5.0

# Step 4: Verify
echo "Verifying rollback..."
python -c "
from claw_mem import MemoryManager
mm = MemoryManager()
mm.start_session('rollback_auto')
print('✅ Rollback successful')
mm.end_session()
"

echo ""
echo "✅ Rollback to v0.5.0 completed"
echo "Backup used: $LATEST_BACKUP"
```

### Usage

```bash
# Make executable
chmod +x rollback_to_v050.sh

# Execute rollback
./rollback_to_v050.sh
```

---

## Post-Rollback Actions

### 1. Document Issues

Create issue report:

```bash
cat > ~/claw-mem-v060-issues.txt << EOF
Date: $(date)
Version: v0.6.0
Issues Encountered:

1. [Describe issue 1]
2. [Describe issue 2]
3. [Describe issue 3]

Impact: [Describe impact on workflow]

Rollback Status: COMPLETED
Backup Used: [Backup directory]
EOF
```

### 2. Report Issues (Optional)

Submit to GitHub:

```bash
# Open GitHub issue
open https://github.com/opensourceclaw/claw-mem/issues/new
```

### 3. Monitor v0.5.0 Stability

```bash
# Create monitoring log
cat >> ~/claw-mem-v050-monitor.log << EOF
Date: $(date)
Action: Rollback from v0.6.0
Status: Monitoring for stability
EOF
```

---

## Troubleshooting

### Issue 1: Backup Not Found

**Symptom**: `No backup found`

**Solution**:
```bash
# Search for backup files
find ~ -name "claw-mem-backup-*" -type d 2>/dev/null

# If truly missing, create emergency backup before rollback
mkdir -p ~/claw-mem-emergency-backup
cp -r ~/.openclaw/workspace/MEMORY.md ~/claw-mem-emergency-backup/ 2>/dev/null || true
cp -r ~/.openclaw/workspace/memory/ ~/claw-mem-emergency-backup/ 2>/dev/null || true
```

### Issue 2: Memory Files Not Restored

**Symptom**: `MEMORY.md not found after rollback`

**Solution**:
```bash
# Check backup contents
ls -la ~/claw-mem-backup-*/

# Manually restore
cp ~/claw-mem-backup-*/MEMORY.md ~/.openclaw/workspace/
cp -r ~/claw-mem-backup-*/memory/ ~/.openclaw/workspace/
```

### Issue 3: v0.5.0 Installation Failed

**Symptom**: `ERROR: Could not find a version that satisfies the requirement claw-mem==0.5.0`

**Solution**:
```bash
# Check available versions
pip index versions claw-mem

# Install latest available version
pip install claw-mem==0.5.0

# If 0.5.0 not available, use latest
pip install claw-mem
```

---

## Rollback Checklist

### Pre-Rollback

- [ ] Document current issues
- [ ] Locate backup directory
- [ ] Verify backup integrity
- [ ] Create emergency backup (if needed)

### During Rollback

- [ ] Uninstall v0.6.0
- [ ] Restore memory files from backup
- [ ] Install v0.5.0
- [ ] Verify installation

### Post-Rollback

- [ ] Test import
- [ ] Verify memory continuity
- [ ] Test search functionality
- [ ] Document rollback completion
- [ ] Report issues (optional)

---

## Support

If rollback fails or you need assistance:

- **Documentation**: https://github.com/opensourceclaw/claw-mem/tree/main/docs
- **Issues**: https://github.com/opensourceclaw/claw-mem/issues
- **Emergency Contact**: [Project maintainer contact]

---

**End of Rollback Procedure**
