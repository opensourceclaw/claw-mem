# Apache 2.0 License Configuration Guide

**Version**: 1.0  
**Last Updated**: 2026-03-23  
**Status**: ✅ Complete  

---

## 📋 Overview

This guide documents the Apache 2.0 License configuration for claw-mem project.

claw-mem is licensed under the **Apache License 2.0**, a permissive open-source license that provides:

- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Patent use allowed
- ✅ Private use allowed
- ⚠️ License and copyright notice required
- ⚠️ State changes required
- ⚠️ Disclose source (when distributing)

---

## 📄 License Files

### 1. LICENSE (Root Directory)

**Location**: `/Users/liantian/workspace/osprojects/claw-mem/LICENSE`

**Content**: Full Apache 2.0 License text (11,357 bytes)

**Status**: ✅ Complete

---

### 2. NOTICE (Root Directory)

**Location**: `/Users/liantian/workspace/osprojects/claw-mem/NOTICE`

**Purpose**: Attribution notices required by Apache 2.0 Section 4(d)

**Current Content**:
```
claw-mem
Copyright 2026 Peter Cheng

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
```

**Status**: ✅ Complete

---

### 3. pyproject.toml License Declaration

**Location**: `/Users/liantian/workspace/osprojects/claw-mem/pyproject.toml`

**Configuration**:
```toml
[project]
name = "claw-mem"
version = "0.8.0"
license = "Apache-2.0"
authors = [
    {name = "Peter Cheng"}
]
```

**Status**: ✅ Complete

---

### 4. Source Code Headers

**Required Format** (for all Python files):
```python
# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```

**Implementation Status**: 🔄 In Progress

**Files to Update**:
- [ ] `src/claw_mem/__init__.py`
- [ ] `src/claw_mem/memory_manager.py`
- [ ] `src/claw_mem/config.py`
- [ ] `src/claw_mem/errors.py`
- [ ] All other `.py` files in `src/`

---

## 🔍 Apache 2.0 Compliance Checklist

### ✅ Completed

- [x] LICENSE file in root directory
- [x] NOTICE file with copyright attribution
- [x] License declared in pyproject.toml
- [x] 100% English documentation (v0.9.0+)
- [x] Clear copyright statement

### 🔄 In Progress

- [ ] Source code headers in all Python files
- [ ] Header in documentation files (optional but recommended)
- [ ] Third-party dependency attribution (if applicable)

### 📋 Recommended

- [ ] Add license badge to README.md
- [ ] Add license section to CONTRIBUTING.md
- [ ] Create THIRD-PARTY-NOTICES for dependencies

---

## 🏷️ License Badge

Add to README.md:

```markdown
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
```

**Placement**: After project title, before description

---

## 📦 PyPI License Configuration

The `pyproject.toml` is already configured correctly for PyPI:

```toml
[project]
license = "Apache-2.0"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
```

**PyPI License Display**: ✅ Will show "Apache 2.0" on PyPI page

---

## 🔧 Automated Header Addition

### Script: `scripts/add_license_headers.py`

Create this script to add headers to all Python files:

```python
#!/usr/bin/env python3
"""
Add Apache 2.0 license headers to all Python files.
"""

import os
from pathlib import Path

LICENSE_HEADER = """# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""

def add_header_to_file(filepath: Path) -> bool:
    """Add license header if not present."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has header
    if 'Licensed under the Apache License' in content:
        return False
    
    # Add header
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(LICENSE_HEADER + content)
    
    return True

def main():
    src_dir = Path(__file__).parent.parent / 'src'
    count = 0
    
    for py_file in src_dir.rglob('*.py'):
        if add_header_to_file(py_file):
            print(f"Added header: {py_file}")
            count += 1
    
    print(f"\nTotal files updated: {count}")

if __name__ == '__main__':
    main()
```

**Usage**:
```bash
cd /Users/liantian/workspace/osprojects/claw-mem
python scripts/add_license_headers.py
```

---

## 📊 License Compliance Status

| Component | Status | Notes |
|-----------|--------|-------|
| LICENSE file | ✅ Complete | Full Apache 2.0 text |
| NOTICE file | ✅ Complete | Copyright attribution |
| pyproject.toml | ✅ Complete | License declared |
| README.md badge | ⏳ Pending | Add license badge |
| Source headers | ⏳ Pending | Run script to add |
| Documentation headers | ⏳ Optional | Recommended for docs |
| THIRD-PARTY-NOTICES | ⏳ Optional | If using third-party code |

---

## 🎯 Next Steps

### Immediate (Before v1.0.0 Release)

1. ✅ Review this guide
2. ⏳ Run license header script
3. ⏳ Add license badge to README.md
4. ⏳ Verify all files have headers

### Before PyPI Release

1. ⏳ Final compliance check
2. ⏳ Create THIRD-PARTY-NOTICES (if needed)
3. ⏳ Test PyPI upload with license metadata
4. ⏳ Verify license displays correctly on PyPI

---

## 📚 References

- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- [Apache 2.0 Tutorial](https://www.apache.org/licenses/LICENSE-2.0.html)
- [SPDX License Identifier](https://spdx.org/licenses/Apache-2.0.html)
- [PyPI License Classifiers](https://pypi.org/classifiers/)

---

## ✅ Compliance Verification

Run this checklist before release:

```bash
# 1. Verify LICENSE exists
test -f LICENSE && echo "✅ LICENSE exists" || echo "❌ LICENSE missing"

# 2. Verify NOTICE exists
test -f NOTICE && echo "✅ NOTICE exists" || echo "❌ NOTICE missing"

# 3. Check pyproject.toml license
grep -q 'license = "Apache-2.0"' pyproject.toml && \
  echo "✅ pyproject.toml license declared" || \
  echo "❌ pyproject.toml license missing"

# 4. Count files with headers
echo "Files with license headers:"
grep -r "Licensed under the Apache License" src/ | wc -l
```

---

**Author**: Friday (Business Agent)  
**Reviewer**: Peter (Pending)  
**Last Updated**: 2026-03-23  

---

*claw-mem - Make OpenClaw Truly Remember*  
*Project Neo - Est. 2026*  
*"Ad Astra Per Aspera"*
