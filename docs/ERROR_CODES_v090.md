# claw-mem Error Codes

**Version**: 0.9.0  
**Language**: English  
**Last Updated**: 2026-03-21  
**Status**: Active  

---

## 📖 Error Code Reference

All errors in claw-mem are friendly, actionable, and in English (v0.9.0+).

### INDEX_NOT_FOUND

**Description**: Memory index file not found

**Causes**:
- First startup, index not yet built
- Index file accidentally deleted
- Index path misconfigured

**Solution**:

System will automatically rebuild index, just wait (about 1 second)

**Example**:
```
[Error] Memory index not found, rebuilding...
[Suggestion] First startup needs to rebuild index, please wait (about 1 second)
[Error Code] INDEX_NOT_FOUND
```

---

### WORKSPACE_NOT_FOUND

**Description**: OpenClaw workspace not found

**Causes**:
- OpenClaw not installed
- Workspace path misconfigured
- Running from wrong directory

**Solution**:

Confirm OpenClaw is properly installed, or manually specify workspace path

**Example**:
```
[Error] OpenClaw workspace not found
[Suggestion] Please confirm OpenClaw is properly installed, or manually specify workspace path
[Error Code] WORKSPACE_NOT_FOUND
```

---

### MEMORY_CORRUPTED

**Description**: Memory file corrupted, attempting to restore from backup...

**Causes**:
- Disk errors
- Interrupted write operation
- File system corruption

**Solution**:

System will automatically restore from nearest backup. If this persists, check disk health.

**Example**:
```
[Error] Memory file corrupted, attempting to restore from backup...
[Suggestion] System will automatically restore from nearest backup. If this persists, check disk health.
[Error Code] MEMORY_CORRUPTED
```

---

### PERMISSION_DENIED

**Description**: Permission denied, cannot access file

**Causes**:
- Insufficient file permissions
- Running with wrong user
- File ownership issues

**Solution**:

Check file permissions or use chmod to modify permissions

**Example**:
```
[Error] Permission denied, cannot access file
[Suggestion] Check file permissions or use chmod to modify permissions
[Error Code] PERMISSION_DENIED
```

---

### CONFIGURATION_ERROR

**Description**: Configuration error

**Causes**:
- Invalid configuration format
- Missing required fields
- Type mismatch

**Solution**:

Check configuration file format and required fields

**Example**:
```
[Error] Configuration error
[Suggestion] Check configuration file format and required fields
[Error Code] CONFIGURATION_ERROR
```

---

### MEMORY_RETRIEVAL_ERROR

**Description**: Memory retrieval failed

**Causes**:
- Search index corrupted
- Query processing error
- Memory storage inaccessible

**Solution**:

Try rebuilding index or restarting application

**Example**:
```
[Error] Memory retrieval failed
[Suggestion] Try rebuilding index or restarting application
[Error Code] MEMORY_RETRIEVAL_ERROR
```

---

### VALIDATION_ERROR

**Description**: Validation failed

**Causes**:
- Invalid memory content
- Security pattern detected
- Write validation rejected

**Solution**:

Review memory content and remove invalid patterns

**Example**:
```
[Error] Validation failed
[Suggestion] Review memory content and remove invalid patterns
[Error Code] VALIDATION_ERROR
```

---

### NETWORK_ERROR

**Description**: Network error

**Causes**:
- Network connection unavailable
- Remote service unreachable
- Timeout

**Solution**:

Check network connection and retry

**Example**:
```
[Error] Network error
[Suggestion] Check network connection and retry
[Error Code] NETWORK_ERROR
```

---

### DEPENDENCY_ERROR

**Description**: Dependency error

**Causes**:
- Required package not installed
- Dependency version incompatible
- Import failed

**Solution**:

Install missing dependencies or check version compatibility

**Example**:
```
[Error] Dependency error
[Suggestion] Install missing dependencies or check version compatibility
[Error Code] DEPENDENCY_ERROR
```

---

## 🔧 Getting Error Documentation

Programmatic access to error documentation:

```python
from claw_mem.errors import get_error_documentation

# Get documentation for specific error code
doc = get_error_documentation("INDEX_NOT_FOUND")
print(doc)

# List all error codes
from claw_mem.errors import ERROR_REGISTRY
print(f"Total error codes: {len(ERROR_REGISTRY)}")
```

---

## 📝 Error Message Format

All errors follow this format:

```
[Error] <Human-readable message>
[Suggestion] <Actionable suggestion>
[Error Code] <ERROR_CODE>
```

### Design Principles

1. **Chinese messages** (v0.8.0) / **English messages** (v0.9.0+)
2. **Actionable suggestions** - Tell users what to do
3. **Error codes** - For debugging and documentation
4. **Friendly tone** - No technical jargon

---

*For legacy v0.8.0 Chinese error codes, see ERROR_CODES_v080.md*
