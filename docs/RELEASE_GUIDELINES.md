# claw-mem Release Guidelines
# claw-mem 发布规范

**Version:** 1.0  
**Date:** 2026-03-23  
**Status:** ✅ **ACTIVE**

---

## 🎯 GitHub Release Title Format
## GitHub Release 标题格式

### ✅ Correct Format (正确格式)

```
claw-mem vx.x.x
```

**Examples:**
```
claw-mem v1.0.0
claw-mem v1.0.1
claw-mem v1.1.0
claw-mem v2.0.0
```

### ❌ Incorrect Format (错误格式)

```
claw-mem v1.0.0 - Three-Tier Memory Retrieval  ❌
claw-mem v1.0.1 - Stability & Bug Fixes  ❌
claw-mem v1.0.0 (Major Release)  ❌
claw-mem v1.0.0 [Stable]  ❌
```

**Rule:** **Only `claw-mem vx.x.x`, no additional text!**
**规则:** **仅 `claw-mem vx.x.x`，不加任何额外文字！**

---

## 📋 Release Checklist
## 发布清单

### Pre-Release
### 发布前

- [ ] **Version bumped** in `src/claw_mem/__init__.py`
- [ ] **CHANGELOG.md** updated
- [ ] **All tests passing** (`pytest tests/ -v`)
- [ ] **Documentation updated**
- [ ] **Git commit** with proper message
- [ ] **Git tag** created (`git tag -a vx.x.x -m "claw-mem vx.x.x"`)

### Release
### 发布中

- [ ] **Git push** (`git push origin main`)
- [ ] **Tag push** (`git push origin vx.x.x`)
- [ ] **GitHub Release** created
  - **Title:** `claw-mem vx.x.x` (EXACTLY!)
  - **Notes:** Use `RELEASE_NOTES_vx.x.x.md`
  - **Tag:** vx.x.x
- [ ] **Release verified** on GitHub

### Post-Release
### 发布后

- [ ] **Installation tested**
- [ ] **Version verified** (`import claw_mem; print(claw_mem.__version__)`)
- [ ] **Basic functionality tested**
- [ ] **Documentation deployed**

---

## 🚀 Release Commands
## 发布命令

### Standard Release Process
### 标准发布流程

```bash
# 1. Update version
echo '__version__ = "1.0.1"' > src/claw_mem/__init__.py

# 2. Commit
git add -A
git commit -m "chore: Release v1.0.1"

# 3. Tag
git tag -a v1.0.1 -m "claw-mem v1.0.1"

# 4. Push
git push origin main
git push origin v1.0.1

# 5. GitHub Release
gh release create v1.0.1 \
  --title "claw-mem v1.0.1" \
  --notes-file docs/RELEASE_NOTES_v101.md \
  --repo opensourceclaw/claw-mem

# 6. Verify
python3 -c "import claw_mem; print(claw_mem.__version__)"
```

---

## 🎯 Version Numbering
## 版本号规则

### Semantic Versioning (SemVer)
### 语义化版本

```
MAJOR.MINOR.PATCH
  ↓     ↓      ↓
  1  .  0  .  1
  
MAJOR: Breaking changes
MINOR: New features (backward compatible)
PATCH: Bug fixes (backward compatible)
```

---

## 🎯 Best Practices
## 最佳实践

### DO ✅
### 应该做

- ✅ Use exact format: `claw-mem vx.x.x`
- ✅ Keep release notes concise
- ✅ Test before release
- ✅ Document breaking changes
- ✅ Use semantic versioning

### DON'T ❌
### 不应该做

- ❌ Add descriptions to title
- ❌ Skip testing
- ❌ Break backward compatibility (without MAJOR)
- ❌ Forget to update CHANGELOG
- ❌ Release on Friday afternoon

---

*Release Guidelines Created: 2026-03-23*  
*Version:* 1.0  
*Status:* ✅ **ACTIVE**  
*"Ad Astra Per Aspera"*

---

## 🎯 Quick Reference
## 快速参考

```
┌────────────────────────────────────────┐
│  GitHub Release Title Format           │
├────────────────────────────────────────┤
│  ✅ CORRECT:  claw-mem v1.0.1          │
│  ❌ WRONG:    claw-mem v1.0.1 - Fixes  │
│                                        │
│  Rule: ONLY "claw-mem vx.x.x"!         │
└────────────────────────────────────────┘
```
