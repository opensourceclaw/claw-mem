# claw-mem Error Codes

**Version**: 0.9.0  
**Language**: English  
**Last Updated**: 2026-03-22

---

## 📖 Error Code Reference

### INDEX_NOT_FOUND

**Description**: Memory index file not found

**Causes**:
- First startup, index not yet built
- Index file accidentally deleted
- Index path configuration error

**Solution**:
```
System will automatically rebuild index, please wait (~1 second)
```

**Example Output**:
```
[Error] Memory index not found, rebuilding...
[Suggestion] First startup requires index rebuild, please wait (~1 second)
[Error Code] INDEX_NOT_FOUND
[Details] Index path: ~/.claw-mem/index/index_v0.9.0.pkl.gz
```

---

### WORKSPACE_NOT_FOUND

**Description**: OpenClaw workspace not found

**Causes**:
- OpenClaw not installed
- Workspace path configuration error
- Using non-standard workspace path

**Solution**:
```
1. Confirm OpenClaw is correctly installed
2. Check default path: ~/.openclaw/workspace
3. Or manually specify workspace: memory = MemoryManager(workspace="/your/path")
```

**Example Output**:
```
[Error] OpenClaw workspace not found
[Suggestion] Please confirm OpenClaw is installed or manually specify workspace path
[Error Code] WORKSPACE_NOT_FOUND
[Details] Searched paths:
  - ~/.openclaw/workspace
  - ~/.config/openclaw/workspace
  - /current/dir
```

---

### MEMORY_CORRUPTED

**Description**: Memory file corrupted

**Causes**:
- Disk errors
- Unexpected power loss
- File accidentally modified

**Solution**:
```
System will automatically restore from recent backup
If this issue persists, please check disk health
```

**Example Output**:
```
[Error] Memory file corrupted
[Suggestion] Restoring from backup, please wait
[Error Code] MEMORY_CORRUPTED
[Details] File: ~/.claw-mem/memories/MEMORY.md
```

---

### CONFIG_INVALID

**Description**: Configuration file invalid

**Causes**:
- Syntax errors in config file
- Missing required fields
- Invalid values

**Solution**:
```
1. Check config file syntax
2. Verify required fields are present
3. Use default config as reference
```

**Example Output**:
```
[Error] Configuration file invalid
[Suggestion] Please check config syntax and required fields
[Error Code] CONFIG_INVALID
[Details] ~/.claw-mem/config.yml: line 15, column 3
```

---

### RETRIEVAL_TIMEOUT

**Description**: Retrieval operation timed out

**Causes**:
- Very large index
- System resource constraints
- Complex query

**Solution**:
```
1. Wait for operation to complete
2. Consider splitting large queries
3. Check system resources
```

**Example Output**:
```
[Error] Retrieval operation timed out
[Suggestion] Query is taking longer than expected, please wait
[Error Code] RETRIEVAL_TIMEOUT
[Details] Timeout: 30 seconds, Query length: 5000 chars
```

---

### BACKUP_FAILED

**Description**: Backup operation failed

**Causes**:
- Insufficient disk space
- Permission errors
- File locked by another process

**Solution**:
```
1. Check available disk space
2. Verify file permissions
3. Close other applications using the file
```

**Example Output**:
```
[Error] Backup operation failed
[Suggestion] Please check disk space and file permissions
[Error Code] BACKUP_FAILED
[Details] Target: ~/.claw-mem/backups/memory_20260322_120000.bak
```

---

### RECOVERY_FAILED

**Description**: Recovery operation failed

**Causes**:
- No valid backup found
- Backup file corrupted
- Recovery process interrupted

**Solution**:
```
1. Check backup files exist
2. Manually restore from backup if needed
3. Contact support if issue persists
```

**Example Output**:
```
[Error] Recovery operation failed
[Suggestion] No valid backup found, manual intervention required
[Error Code] RECOVERY_FAILED
[Details] Searched 3 backup files, all invalid
```

---

### INDEX_LOAD_FAILED

**Description**: Index loading failed

**Causes**:
- Index file corrupted
- Version mismatch
- Memory constraints

**Solution**:
```
System will attempt to rebuild index automatically
If rebuild fails, manual intervention required
```

**Example Output**:
```
[Error] Index loading failed
[Suggestion] Attempting automatic rebuild...
[Error Code] INDEX_LOAD_FAILED
[Details] Index version: 0.8.0, Expected: 0.9.0
```

---

### HEALTH_CHECK_FAILED

**Description**: Health check detected issues

**Causes**:
- Disk space low
- Memory usage high
- Expired memories not cleaned

**Solution**:
```
Review health report and follow recommendations
Auto-cleanup will run if enabled
```

**Example Output**:
```
[Warning] Health check detected issues
[Suggestion] Review health report for details
[Error Code] HEALTH_CHECK_FAILED
[Details] 3 issues found: disk space, memory usage, expired memories
```

---

### CACHE_ERROR

**Description**: Cache operation failed

**Causes**:
- Cache corrupted
- Memory limits exceeded
- Cache eviction failed

**Solution**:
```
Cache will be automatically cleared and rebuilt
Performance may be temporarily degraded
```

**Example Output**:
```
[Warning] Cache operation failed
[Suggestion] Clearing and rebuilding cache
[Error Code] CACHE_ERROR
[Details] L1 cache corrupted, L2 cache cleared
```

---

## 🔧 Error Handling Best Practices

### For Users

1. **Read Error Messages Carefully**
   - Error code identifies the issue
   - Suggestion provides next steps
   - Details give technical context

2. **Follow Suggested Solutions**
   - Most errors have automatic recovery
   - Manual intervention rarely needed
   - Contact support if issues persist

3. **Keep Backups**
   - Regular backups prevent data loss
   - Multiple backup versions retained
   - Easy to restore from backup

### For Developers

1. **Use Specific Error Codes**
   - Each error type has unique code
   - Consistent naming convention
   - Clear error hierarchy

2. **Provide Actionable Suggestions**
   - Tell users what to do next
   - Include example commands
   - Link to documentation

3. **Log Detailed Context**
   - Include file paths
   - Show relevant values
   - Capture stack traces

---

## 📊 Error Code Categories

| Category | Prefix | Count | Severity |
|----------|--------|-------|----------|
| **Index Errors** | INDEX_* | 3 | High |
| **Workspace Errors** | WORKSPACE_* | 1 | High |
| **Memory Errors** | MEMORY_* | 2 | High |
| **Config Errors** | CONFIG_* | 1 | Medium |
| **Retrieval Errors** | RETRIEVAL_* | 1 | Medium |
| **Backup Errors** | BACKUP_* | 1 | Medium |
| **Recovery Errors** | RECOVERY_* | 1 | High |
| **Health Errors** | HEALTH_* | 1 | Low |
| **Cache Errors** | CACHE_* | 1 | Low |

---

## 🆕 New in v0.9.0

### Added Error Codes

- `HEALTH_CHECK_FAILED` - Health check detected issues
- `CACHE_ERROR` - Cache operation failed
- `INDEX_LOAD_FAILED` - Index loading failed
- `CONFIG_INVALID` - Configuration file invalid

### Improved Error Messages

- More specific suggestions
- Better technical details
- Consistent formatting
- 100% English

---

*Document Version: 0.9.0*  
*Language: English*  
*Last Updated: 2026-03-22*  
*claw-mem Project - Est. 2026*  
*"Ad Astra Per Aspera"*
