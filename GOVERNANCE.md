# Governance

This document defines the governance structure for the claw-mem project.

## Roles

### Maintainer

Maintainers have commit access and are responsible for:
- Reviewing and merging pull requests
- Triaging issues and feature requests
- Managing releases and versioning
- Enforcing the Code of Conduct
- Making architectural decisions

**Current Maintainer**: Friday (Project Lead)

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

### BDFL Model

claw-mem currently operates under a BDFL (Benevolent Dictator For Life) model with Friday as the project lead. Major decisions are made by the BDFL after consulting contributors.

### Technical Decisions

- **RFC Process**: Major architectural changes require an RFC (Request for Comments)
- **Consensus Seeking**: Discussion on issues/PRs before merging significant changes
- **Lazy Consensus**: Small fixes may be merged with one approval if no objections within 48 hours

### Release Process

1. **Alpha**: Internal testing, feature-complete
2. **Beta**: Feature freeze, bug fixes only
3. **Release Candidate**: Final testing, documentation updates
4. **Stable**: Tagged release, published to npm and GitHub Releases

Each release requires:
- Zero TypeScript build errors
- All tests passing
- CHANGELOG updated
- Version bumped in `package.json`

## Conflict Resolution

1. Discussion between involved parties on the relevant issue or PR
2. Escalation to a maintainer for mediation
3. Final decision by the BDFL if consensus cannot be reached

---

*Last updated: 2026-06-13*
