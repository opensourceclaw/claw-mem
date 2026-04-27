# claw-mem Release Process (Complete with Deployment)

**Version:** 1.0  
**Created:** 2026-03-24  
**Status:** ✅ Active  
**License:** Apache-2.0  
**Documentation Standard:** 100% English (Apache International Open Source Standard)  

---

## 📋 Standard Release Process

### Phase 1: Pre-Release Preparation

- [ ] **Version Confirmed** - Follow semantic versioning (v{major}.{minor}.{patch})
- [ ] **Tests Passed** - All unit and integration tests passing (>90% coverage)
- [ ] **CHANGELOG.md Updated** - Document all changes
- [ ] **README.md Updated** - Update version and key features
- [ ] **Code Merged to main** - Ensure main branch is latest
- [ ] **Local Build Tested** - `pip install -e .` successful
- [ ] **Release Notes Drafted** - Complete release notes (100% English)
- [ ] **User Approval Obtained** - Peter approves release

### Phase 2: Git Tag Creation

```bash
# 1. Checkout main branch
git checkout main
git pull origin main

# 2. Create annotated tag (Apache standard requires annotated)
git tag -a <VERSION> -m "<TITLE>"

# 3. Push tag to remote
git push origin <VERSION>
```

**Key Points:**
- MUST use `git tag -a` (annotated tag)
- NOT lightweight tag
- Tag format: `v1.0.2`

### Phase 3: GitHub Release Creation

```bash
gh release create <VERSION> \
  --repo opensourceclaw/claw-mem \
  --title "<TITLE>" \
  --notes-file RELEASE_NOTES.md \
  --verify-tag
```

**Required Fields:**
- Tag: `v1.0.2`
- Title: `claw-mem v1.0.2`
- Release Notes: From `RELEASE_NOTES_v1.0.2.md`
- Verify Tag: `--verify-tag`

### Phase 4: DEPLOY TO SYSTEM ⚠️ CRITICAL (Previously Missing!)

**CRITICAL LESSON LEARNED:** Previous releases (v0.5.0, v0.6.0, v1.0.1) created GitHub Releases but NEVER deployed to system! This step is MANDATORY.

```bash
# Copy new version to OpenClaw skills directory
cp -r /Users/liantian/workspace/claw-mem/core \
      /Users/liantian/workspace/claw-mem/tests \
      /Users/liantian/workspace/claw-mem/*.md \
      ~/.openclaw/workspace/skills/claw-mem/

# Alternative: Create symlinks (for development)
ln -sf /Users/liantian/workspace/claw-mem/core \
        ~/.openclaw/workspace/skills/claw-mem/core
ln -sf /Users/liantian/workspace/claw-mem/tests \
        ~/.openclaw/workspace/skills/claw-mem/tests

# Verify deployment
ls -la ~/.openclaw/workspace/skills/claw-mem/core/
ls -la ~/.openclaw/workspace/skills/claw-mem/tests/
```

**Verification Checklist:**
- [ ] `core/` directory exists in system skills
- [ ] `tests/` directory exists in system skills
- [ ] Release notes copied to system
- [ ] Old version backed up (optional)

### Phase 5: Post-Release Verification

```bash
# Run tests on deployed version
cd ~/.openclaw/workspace/skills/claw-mem
python3 -m pytest tests/ -v

# Verify version number
cat RELEASE_NOTES_v1.0.2.md | grep "^Version:"

# Test core functionality
python3 -c "from core.memory_v1_0_2 import MemorySystem; print('✅ v1.0.2 deployed successfully')"
```

**Verification Checklist:**
- [ ] Tests pass on deployed version
- [ ] Version number correct
- [ ] Core functionality works
- [ ] No breaking changes

### Phase 6: Documentation Update

- [ ] Update project documentation
- [ ] Announce release to users
- [ ] Update release tracker
- [ ] Archive old release notes (if needed)

---

## ⚠️ Critical Rules (MUST Follow)

### Rule 1: Complete Release Process

**NEVER skip deployment step!**

```
✅ Complete: GitHub Release + Deploy to System
❌ Incomplete: GitHub Release Only (Previous Mistake!)
```

### Rule 2: Apache Documentation Standard

**ALL documentation and code MUST be 100% English:**
- ✅ Code comments: 100% English
- ✅ Documentation: 100% English
- ✅ Tests: 100% English
- ✅ Release Notes: 100% English

### Rule 3: Project Workspace Organization

**Keep project docs organized:**
- Project Docs → `docs/` directory
- Release Docs → Project root directory
- Core Code → `core/` directory
- Tests → `tests/` directory
- **NEVER mix:** Project docs across different project directories

---

## 🎯 Release Checklist Template

### Pre-Release Confirmation

- [ ] Code complete (100% English comments)
- [ ] All tests passing (>90% coverage)
- [ ] Performance benchmarks met
- [ ] Documentation complete (100% English)
- [ ] Live verification passed
- [ ] Apache License included
- [ ] User approval obtained

### Release Execution

- [ ] Git commit created
- [ ] Git tag created (annotated)
- [ ] Tag pushed to GitHub
- [ ] GitHub Release created
- [ ] **DEPLOYED TO SYSTEM** ⚠️ CRITICAL
- [ ] Deployment verified

### Post-Release

- [ ] Tests pass on deployed version
- [ ] Version confirmed correct
- [ ] Documentation updated
- [ ] Users announced

---

## 📚 Historical Release Records

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| v1.0.2 | 2026-03-24 | 📋 Planned | Complete release process with deployment |
| v1.0.1 | ? | ⚠️ Incomplete | GitHub release created, deployment unknown |
| v0.6.0 | 2026-03-18 | ⚠️ Incomplete | GitHub release created, NO deployment |
| v0.5.0 | 2026-03-18 | ⚠️ Incomplete | GitHub release created, NO deployment |

**Lesson Learned:** Always include Phase 4 (Deploy to System)!

---

## 🔧 Automation Scripts (Future)

```bash
#!/bin/bash
# scripts/release.sh

set -e

VERSION=$1
NOTES_FILE=$2

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> <notes_file>"
    exit 1
fi

echo "🚀 Starting release process for $VERSION..."

# Phase 1: Pre-release checks
echo "✅ Phase 1: Running tests..."
python3 -m pytest tests/ -v

# Phase 2: Git tag
echo "🏷️  Phase 2: Creating tag..."
git tag -a $VERSION -m "claw-mem $VERSION"
git push origin $VERSION

# Phase 3: GitHub Release
echo "📦 Phase 3: Creating GitHub Release..."
gh release create $VERSION --notes-file $NOTES_FILE --verify-tag

# Phase 4: Deploy to System (CRITICAL!)
echo "📥 Phase 4: Deploying to system..."
cp -r core tests *.md ~/.openclaw/workspace/skills/claw-mem/
echo "✅ Deployed to ~/.openclaw/workspace/skills/claw-mem/"

# Phase 5: Verify
echo "🧪 Phase 5: Verifying deployment..."
cd ~/.openclaw/workspace/skills/claw-mem
python3 -m pytest tests/ -v

echo "🎉 Release $VERSION completed successfully!"
```

---

*Document Created: 2026-03-24T16:10+08:00*  
*Version: 1.0*  
*Status: ✅ Active*  
*License: Apache-2.0*  
*Documentation Language: 100% English (Apache Standard)*  
*Critical Lesson: ALWAYS include deployment step!*
