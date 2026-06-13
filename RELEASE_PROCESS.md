# Release Process

This document defines the release process for claw-mem.

## Versioning

claw-mem follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking API changes
- **MINOR** (0.X.0): New features, backward-compatible
- **PATCH** (0.0.X): Bug fixes, backward-compatible

## Release Stages

1. **Alpha**: Internal testing, feature-complete
2. **Beta**: Feature freeze, bug fixes only
3. **Release Candidate**: Final testing, documentation updates
4. **Stable**: Tagged release, published to npm and GitHub Releases

## Release Checklist

### Pre-Release

- [ ] `npm run build` — zero TypeScript errors
- [ ] `npm test` — all tests passing (≥ 99.8% pass rate)
- [ ] `npm audit --production` — zero vulnerabilities
- [ ] CHANGELOG.md updated with all changes
- [ ] README.md version badge updated
- [ ] Version bumped in `package.json`
- [ ] Version bumped in `claw_mem_plugin/package.json`
- [ ] All new public APIs have TSDoc comments

### Tag Creation

```bash
# Create annotated tag
git tag -a vX.Y.Z <commit> -m "vX.Y.Z: <description>"

# Push tag to remote
git push origin vX.Y.Z

# Verify
git ls-remote origin | grep vX.Y.Z
```

### GitHub Release

1. Go to [GitHub Releases](https://github.com/opensourceclaw/claw-mem/releases)
2. Click "Draft a new release"
3. Choose the tag `vX.Y.Z`
4. Title: `vX.Y.Z — <summary>`
5. Copy relevant CHANGELOG section as release notes
6. Attach SBOM if available (`sbom.json` or `sbom.xml`)

### Post-Release

- [ ] Verify tag is visible on remote: `git ls-remote origin | grep vX.Y.Z`
- [ ] Verify npm package (if published)
- [ ] Announce in relevant channels

## Breaking Changes

- Must be documented in CHANGELOG under `### Breaking Changes`
- Require a major version bump
- Migration guide must be provided in the release notes

## Hotfix Process

For critical bugs in the current stable release:

1. Create a fix branch from the stable tag
2. Develop and test the fix
3. Bump PATCH version
4. Follow standard release checklist
5. Cherry-pick fix to main if needed

---

*Last updated: 2026-06-13*
