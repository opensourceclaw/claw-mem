# Installation Issue Analysis & Fix

> Date: 2026-04-17
> Issue: Users cannot install claw-mem and claw-rl via pip/npm

---

## 🔴 Problem Identified

### 1. Python Package NOT on PyPI

```bash
$ pip install claw-mem
ERROR: No matching distribution found for claw-mem
```

**Root Cause**: Package only exists locally (editable install), not published to PyPI.

**Current State**:
```
Location: /Users/liantian/workspace/osprojects/claw-mem (editable)
PyPI: ❌ NOT PUBLISHED
```

### 2. npm Package NOT on npm Registry

```bash
$ npm install @opensourceclaw/openclaw-claw-mem
npm error 404 Not Found
```

**Root Cause**: Package not published to npm registry.

**Current State**:
```
npm Registry: ❌ NOT PUBLISHED
```

---

## ✅ Fix Options

### Option A: Publish to PyPI and npm (Recommended)

**Python Package (PyPI):**

```bash
# Build package
cd /Users/liantian/workspace/osprojects/claw-mem
python3 -m build

# Upload to PyPI
python3 -m twine upload dist/claw_mem-2.0.0*

# Verify
pip install claw-mem --dry-run
```

**npm Package:**

```bash
cd /Users/liantian/workspace/osprojects/claw-mem/claw_mem_plugin
npm login
npm publish --access public

# Verify
npm view @opensourceclaw/openclaw-claw-mem
```

### Option B: Update README with Correct Installation Methods

If packages are not ready for public release, update README with GitHub installation:

```markdown
## 📦 Installation

### Python Package

```bash
# Install from GitHub
pip install git+https://github.com/opensourceclaw/claw-mem.git

# Or clone and install locally
git clone https://github.com/opensourceclaw/claw-mem.git
cd claw-mem
pip install -e .
```

### OpenClaw Plugin

```bash
# Install from GitHub
npm install github:opensourceclaw/claw-mem#main --prefix claw_mem_plugin

# Or clone and link
git clone https://github.com/opensourceclaw/claw-mem.git
cd claw-mem/claw_mem_plugin
npm link
```
```

### Option C: ClawHub Skill Only (Current State)

Since skills are published to ClawHub, update README to focus on skill installation:

```markdown
## 📦 Installation

### Via ClawHub (Recommended)

```bash
# Install skill
npx clawhub@latest install opensourceclaw-claw-mem

# Requires Python package
pip install git+https://github.com/opensourceclaw/claw-mem.git
```

### Manual Installation

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for detailed instructions.
```

---

## 🔧 Immediate Fix Required

### 1. Update README.md

**Before:**
```bash
pip install claw-mem
npm install @opensourceclaw/openclaw-claw-mem
```

**After:**
```bash
# Install from GitHub
pip install git+https://github.com/opensourceclaw/claw-mem.git

# Or via ClawHub (recommended)
npx clawhub@latest install opensourceclaw-claw-mem
```

### 2. Add INSTALLATION.md

Create detailed installation guide with:
- Prerequisites
- Multiple installation methods
- Troubleshooting
- Platform-specific notes

### 3. Publish to PyPI (If Ready)

```bash
# Setup PyPI credentials
python3 -m pip install twine

# Build and upload
python3 -m build
python3 -m twine upload dist/*
```

---

## 📋 Action Items

- [ ] Update README.md with correct installation methods
- [ ] Create docs/INSTALLATION.md with detailed guide
- [ ] Decide: Publish to PyPI or use GitHub installation?
- [ ] Decide: Publish npm package or remove from README?
- [ ] Add installation test to CI/CD
- [ ] Update ClawHub skill description with correct installation

---

## 🚀 Recommended Path

1. **Immediate**: Update README with GitHub installation method
2. **Short-term**: Publish Python package to PyPI
3. **Optional**: Publish npm plugin (if needed for OpenClaw users)

---

## 📝 Same Issue for claw-rl

claw-rl has the same problem:
- Python: Local editable install only
- npm: Not published

Apply the same fix.
