# Auto Configuration Guide

**Version**: 0.8.0  
**Feature**: F002 - Auto Configuration Detection  
**Last Updated**: 2026-03-20

---

## 🎯 Overview

claw-mem v0.8.0 introduces **automatic workspace detection**, eliminating the need for manual configuration.

---

## 🚀 Quick Start

### Before (v0.7.0)

```python
# Manual configuration required
from claw_mem import MemoryManager

mm = MemoryManager(workspace="/Users/liantian/.openclaw/workspace")
```

### After (v0.8.0)

```python
# Auto-detection (recommended)
from claw_mem import MemoryManager

mm = MemoryManager()  # Auto-detects workspace!
```

---

## 📋 How It Works

### Detection Process

```
1. Search default paths (in priority order)
   ├─ ~/.openclaw/workspace
   ├─ ~/.config/openclaw/workspace
   ├─ Current directory
   └─ ~/workspace, ~/projects

2. Check for workspace markers
   ├─ MEMORY.md (core memory file)
   ├─ memory/ (memory directory)
   ├─ AGENTS.md, SOUL.md, USER.md (config files)

3. Return first valid workspace
   └─ Or raise WorkspaceNotFoundError
```

---

## 💡 Usage Examples

### Example 1: Auto-Detection (Recommended)

```python
from claw_mem import MemoryManager

# Automatically detects workspace
mm = MemoryManager()

# Ready to use!
mm.store("User prefers Chinese", memory_type="semantic")
```

---

### Example 2: Manual Override

```python
from claw_mem import MemoryManager

# Manually specify workspace
mm = MemoryManager(workspace="/custom/path")
```

---

### Example 3: Disable Auto-Detection

```python
from claw_mem import MemoryManager

# Disable auto-detection (uses default path)
mm = MemoryManager(auto_detect=False)
```

---

### Example 4: Custom Search Paths

```python
from claw_mem.config import ConfigDetector

# Specify custom search paths
workspace = ConfigDetector.detect_workspace(
    custom_paths=[
        "/path/1",
        "/path/2",
        "~/.openclaw/workspace"
    ]
)

mm = MemoryManager(workspace=workspace)
```

---

## 🔍 Workspace Information

### Get Workspace Details

```python
from claw_mem.config import ConfigDetector

# Get detailed workspace info
info = ConfigDetector.get_workspace_info("/Users/liantian/.openclaw/workspace")

print(f"Path: {info['path']}")
print(f"Exists: {info['exists']}")
print(f"Valid: {info['is_valid']}")
print(f"Markers: {info['markers_found']}")
print(f"Memory files: {info['memory_files'][:5]}")
```

### Example Output

```
Path: /Users/liantian/.openclaw/workspace
Exists: True
Valid: True
Markers: MEMORY.md, memory/, AGENTS.md, SOUL.md, USER.md
Memory files: 2026-03-20.md, 2026-03-19.md, entities.md
```

---

## ⚠️ Error Handling

### Workspace Not Found

```python
from claw_mem import MemoryManager, WorkspaceNotFoundError

try:
    mm = MemoryManager()
except WorkspaceNotFoundError as e:
    print(e)
    # [错误] 未找到 OpenClaw 工作区
    # [建议] 请确认已正确安装 OpenClaw,或手动指定工作区路径
    # [错误码] WORKSPACE_NOT_FOUND
```

### Manual Fallback

```python
from claw_mem import MemoryManager

# Auto-detect fails, use manual path
try:
    mm = MemoryManager()
except WorkspaceNotFoundError:
    mm = MemoryManager(workspace="/manual/path")
```

---

## 🛠️ Advanced Features

### Suggest Workspace Path

```python
from claw_mem.config import ConfigDetector

# Get suggested workspace path (creates if needed)
suggested = ConfigDetector.suggest_workspace()

if suggested:
    print(f"💡 Suggested: {suggested}")
else:
    print("❌ Cannot create suggested workspace")
```

---

### Validate Workspace

```python
from pathlib import Path
from claw_mem.config import ConfigDetector

path = Path("~/.openclaw/workspace").expanduser()
is_valid = ConfigDetector._is_valid_workspace(path)

if is_valid:
    print("✅ Valid workspace")
else:
    print("❌ Invalid workspace")
```

---

## 📊 Detection Performance

| Metric | Value |
|--------|-------|
| **Detection Time** | <10ms |
| **Search Paths** | 5 default |
| **Markers Checked** | 5 files/dirs |
| **Success Rate** | >90% (standard installs) |

---

## 🎯 Best Practices

### ✅ Do

```python
# Use auto-detection (simplest)
mm = MemoryManager()

# Handle errors gracefully
try:
    mm = MemoryManager()
except WorkspaceNotFoundError:
    # Fallback logic
    pass

# Check workspace info before operations
info = ConfigDetector.get_workspace_info(workspace)
if not info['is_valid']:
    # Handle invalid workspace
    pass
```

### ❌ Don't

```python
# Don't hardcode paths (unless necessary)
mm = MemoryManager(workspace="/very/specific/path")

# Don't ignore errors
mm = MemoryManager()  # May raise WorkspaceNotFoundError

# Don't skip validation for critical operations
```

---

## 🔧 Troubleshooting

### Problem: Auto-detection fails

**Symptoms**:
```
WorkspaceNotFoundError: 未找到 OpenClaw 工作区
```

**Solutions**:
1. Verify OpenClaw is installed: `openclaw --version`
2. Check default path exists: `ls ~/.openclaw/workspace`
3. Manually specify workspace: `MemoryManager(workspace="/path")`

---

### Problem: Wrong workspace detected

**Symptoms**:
```
Detected workspace is not the expected one
```

**Solutions**:
1. Use manual override: `MemoryManager(workspace="/correct/path")`
2. Remove invalid markers from wrong directory
3. Add MEMORY.md to correct directory

---

### Problem: Slow detection

**Symptoms**:
```
Initialization takes >1 second
```

**Solutions**:
1. Reduce search paths: `detect_workspace(custom_paths=[...])`
2. Ensure network drives are not in search paths
3. Check for slow filesystem (e.g., encrypted drives)

---

## 📚 API Reference

### ConfigDetector Class

#### `detect_workspace(custom_paths=None)`

Detect OpenClaw workspace path.

**Parameters**:
- `custom_paths` (Optional[List[str]]): Custom search paths

**Returns**:
- `str`: Detected workspace path

**Raises**:
- `WorkspaceNotFoundError`: If no valid workspace found

---

#### `get_workspace_info(workspace_path)`

Get detailed workspace information.

**Parameters**:
- `workspace_path` (str): Workspace path

**Returns**:
- `dict`: Workspace information
  - `path`: Full path
  - `exists`: Whether path exists
  - `is_valid`: Whether it's a valid workspace
  - `markers_found`: List of found markers
  - `memory_files`: List of memory files (max 10)

---

#### `suggest_workspace()`

Suggest a workspace path (creates if needed).

**Returns**:
- `Optional[str]`: Suggested path, or None if cannot create

---

## 🎉 Summary

**Auto configuration detection** makes claw-mem easier to use:

- ✅ **Zero configuration** for most users
- ✅ **Smart detection** with multiple fallback paths
- ✅ **Clear errors** when detection fails
- ✅ **Manual override** for advanced users

**Get started in one line**:
```python
from claw_mem import MemoryManager
mm = MemoryManager()  # That's it!
```

---

**Document Version**: 0.8.0  
**Last Updated**: 2026-03-20  
**Author**: Peter Cheng
