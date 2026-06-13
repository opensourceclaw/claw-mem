# Governance

This document defines the governance structure for the claw-mem project.

## Project Roles (A/B/C Governance)

claw-mem follows a three-role governance model:

| Role | Name | Responsibility |
|------|------|---------------|
| **A** | Friday | Project & Product Management — requirements, acceptance criteria, releases |
| **B** | Jarvis | Product Implementation & Built-in Quality — architecture, development, testing |
| **C** | EDITH | Independent Quality Control — system testing, exploratory testing, release gatekeeping (veto power) |

## Roles

### Maintainer

Maintainers have commit access and are responsible for:
- Reviewing and merging pull requests
- Triaging issues and feature requests
- Managing releases and versioning
- Enforcing the Code of Conduct
- Making architectural decisions

**Current Maintainers**: Friday (Project Lead), Jarvis (Engineering Lead)

### Contributor

Anyone who has contributed code, documentation, bug reports, or other improvements:
- Submit pull requests
- Report and triage issues
- Participate in discussions

### Contributor Promotion Path

1. **First-time Contributor**: Submit a PR (bug fix, doc improvement, etc.)
2. **Regular Contributor**: 3+ merged PRs, active in discussions
3. **Committer**: 10+ merged PRs, demonstrated code review ability — nominated by existing maintainers

## Decision-Making

### Technical Decisions

- **RFC Process**: Major architectural changes require an RFC (Request for Comments)
- **Consensus Seeking**: Maintainers seek consensus before merging significant changes
- **Lazy Consensus**: Small fixes may be merged with one maintainer approval if no objections within 48 hours

### Release Process

1. **Alpha**: Internal testing, feature-complete
2. **Beta**: Feature freeze, bug fixes only
3. **Release Candidate**: Final testing, documentation updates
4. **Stable**: Tagged release, published to npm and GitHub Releases

Each pre-release stage requires:
- Zero TypeScript build errors
- All tests passing
- CHANGELOG updated
- Version bumped in `package.json`

### Breaking Changes

- Must be documented in the CHANGELOG under a `### Breaking Changes` section
- Require a major version bump (e.g., v6.x → v7.0)
- Migration guide must be provided

## Conflict Resolution

1. Discussion between involved parties on the relevant issue or PR
2. Escalation to a maintainer for mediation
3. Final decision by the project lead if consensus cannot be reached

---

*Last updated: 2026-06-13*
