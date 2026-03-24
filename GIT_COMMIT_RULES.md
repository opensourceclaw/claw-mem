# Git Commit Rules for claw-mem

**Version:** 1.0  
**Created:** 2026-03-24  
**Status:** ✅ Active  
**Priority:** P0 (Critical)  

---

## Rule 1: Never Commit docs/ Directory

**Rule:** The `docs/` directory must NEVER be committed to GitHub.

**Rationale:**
- Documentation is for local development and review only
- Reduces repository size
- Prevents accidental publication of draft documentation
- Official documentation should be published separately (e.g., GitHub Pages, website)

**Implementation:**
```gitignore
# .gitignore
docs/
*.md
!README.md
```

**Enforcement:**
- Added to `.gitignore`
- Removed from Git history (`git rm -r --cached docs/`)
- Verified in pre-commit hooks (future enhancement)

---

## Rule 2: Only Commit Essential Files

**What to Commit:**
- ✅ Source code (`core/*.py`, `tests/*.py`, `scripts/*.py`)
- ✅ Configuration files (`pyproject.toml`, `.gitignore`)
- ✅ License (`LICENSE`)
- ✅ README (`README.md`)
- ✅ Release notes (`RELEASE_NOTES_*.md` - for GitHub Releases)

**What NOT to Commit:**
- ❌ Documentation (`docs/` directory)
- ❌ Local configuration (`*.local`, `.env.local`)
- ❌ Build artifacts (`build/`, `dist/`, `*.egg-info/`)
- ❌ Python cache (`__pycache__/`, `*.pyc`)
- ❌ Test artifacts (`.coverage`, `htmlcov/`)
- ❌ Temporary files (`*.tmp`, `*.bak`)

---

## Rule 3: Pre-Commit Checklist

Before each commit, verify:

1. [ ] `docs/` directory is NOT staged
2. [ ] Only essential files are staged
3. [ ] No sensitive information (API keys, passwords)
4. [ ] Commit message follows convention
5. [ ] Tests pass locally

---

## Rule 4: Commit Message Convention

**Format:**
```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation (only README.md)
- `style`: Formatting (no code changes)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Example:**
```
chore: Remove docs/ directory from Git

- Add docs/ to .gitignore
- Remove docs/ from Git history
- Rule: Never commit docs/ to GitHub (local-only documentation)
```

---

## Rule 5: Release Process

**Before Release:**
1. [ ] Verify all changes are committed
2. [ ] Run tests (`python3 tests/run_integration_tests.py`)
3. [ ] Update `RELEASE_NOTES_*.md`
4. [ ] Verify `.gitignore` is up-to-date
5. [ ] Push to GitHub
6. [ ] Create GitHub Release

**After Release:**
1. [ ] Verify GitHub repository (no `docs/` directory)
2. [ ] Verify release notes are published
3. [ ] Monitor for issues (48 hours)

---

## Enforcement

**Automated:**
- `.gitignore` prevents accidental commits
- Pre-commit hooks (future enhancement)

**Manual:**
- Review `git status` before each commit
- Review `git diff --cached` before pushing
- Verify GitHub repository after push

**Violation Recovery:**
If `docs/` is accidentally committed:
```bash
# Remove from Git history
git rm -r --cached docs/
git commit -m "chore: Remove docs/ directory"
git push origin main

# Force push if already pushed (use with caution)
# git push origin main --force
```

---

## Related Documents

- `.gitignore` - Git ignore rules
- `RELEASE_NOTES_*.md` - Release notes (committed)
- `docs/` - Local documentation (NOT committed)

---

*Document Created: 2026-03-24T23:50+08:00*  
*Version: 1.0*  
*Status: ✅ Active*  
*Priority: P0 (Critical)*  
*License: Apache-2.0*
