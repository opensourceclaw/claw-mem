# Contributing to claw-mem

Thank you for considering contributing to claw-mem! 🎉

This guide will help you understand how to participate in this project.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Documentation Language Policy](#documentation-language-policy)
- [What Can I Contribute?](#what-can-i-contribute)
- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Submission Guidelines](#submission-guidelines)
- [Code Review Process](#code-review-process)
- [Release Process](#release-process)

---

## Code of Conduct

This project adopts the [Contributor Covenant 2.1](CODE_OF_CONDUCT.md) as its code of conduct.

Please read and follow it to maintain an open and friendly community environment.

---

## Documentation Language Policy

**Starting from v0.9.0, all documentation and code comments must be in English.**

### Why English?

This policy ensures:
- **Consistency** with Apache 2.0 open source standards
- **Accessibility** for international contributors and users
- **Professional** project maintenance and long-term sustainability
- **Clarity** in technical communication across global community

### What Needs to Be in English?

- ✅ All Markdown documentation files (`.md`)
- ✅ All code comments and docstrings (`.py`)
- ✅ All error messages and user-facing text
- ✅ All test files and scripts
- ✅ All configuration examples

### What About Non-English Content?

- **User data** (memories) - Any language is fine
- **Test data** - Can include non-English examples for testing
- **Translations** - Community translations are welcome as separate files

### Migration from Previous Versions

- **v0.5.0 - v0.8.0**: May contain mixed Chinese/English documentation
- **v0.9.0+**: 100% English documentation policy enforced
- **No breaking changes**: Code behavior remains identical

### Questions?

If you have questions about this policy, please:
1. Open an issue for discussion
2. Check existing issues for similar questions
3. Contact maintainers directly

---

## What Can I Contribute?

### Reporting Bugs

If you find a bug, please create an issue including:

1. **Clear title** - Briefly describe the problem
2. **Reproduction steps** - Help us reproduce the issue
3. **Expected behavior** - What you think should happen
4. **Actual behavior** - What actually happened
5. **Environment info** - Python version, OS, etc.
6. **Logs/screenshots** - Attach error logs or screenshots if available

### Suggesting Features

We welcome feature suggestions! Please create an issue including:

1. **Feature description** - Clearly describe the feature you want
2. **Use case** - What problem does this solve
3. **Implementation ideas** - Share your thoughts if you have any
4. **Alternatives** - Have you considered other solutions?

### Submitting Code

We accept various code contributions:

- 🐛 Bug fixes
- ✨ New features
- 📝 Documentation improvements
- 🧪 Test cases
- 🔧 Performance optimizations
- 🎨 Code refactoring

### Other Ways to Contribute

- 📚 Improve documentation
- 🌍 Translation work
- 💬 Help answer other users' questions
- 📢 Promote the project

---

## Getting Started

### Step 1: Fork the Project

Click the "Fork" button on GitHub to create your own copy.

### Step 2: Clone Locally

```bash
git clone https://github.com/YOUR_USERNAME/claw-mem.git
cd claw-mem
```

### Step 3: Create a Branch

```bash
# Keep in sync with upstream
git remote add upstream https://github.com/yourusername/claw-mem.git
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/amazing-feature
```

**Branch naming conventions:**

- `feature/xxx` - New features
- `fix/xxx` - Bug fixes
- `docs/xxx` - Documentation updates
- `test/xxx` - Test related
- `refactor/xxx` - Code refactoring

### Step 4: Develop and Commit

```bash
# Write code and tests
# ...

# Commit changes
git add .
git commit -m "feat: add amazing feature"
```

**Commit message conventions:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type:**

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation update
- `style` - Code style (no functional change)
- `refactor` - Refactoring
- `test` - Test related
- `chore` - Build/tool related

**Example:**

```bash
git commit -m "feat(memory): add vector search engine

Implement hybrid search with semantic and keyword matching.

Closes #123"
```

### Step 5: Push to Remote

```bash
git push origin feature/amazing-feature
```

### Step 6: Create a Pull Request

1. Visit your forked repository
2. Click "Compare & pull request"
3. Fill in the PR description
4. Wait for code review

---

## Development Environment Setup

### System Requirements

- Python 3.8+
- pip 21.0+
- Git

### Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dev dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_memory.py

# View coverage
pytest --cov=claw_mem --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
# or
start htmlcov/index.html  # Windows
```

### Code Quality Checks

```bash
# Code formatting check
black --check src/ tests/

# Code style check
flake8 src/ tests/

# Type checking
mypy src/

# Auto formatting
black src/ tests/
```

---

## Submission Guidelines

### Code Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for formatting
- Use type hints
- Functions should not exceed 50 lines
- Add appropriate docstrings

### Test Requirements

- All new features must include tests
- Bug fixes must include regression tests
- Test coverage should be at least 80%
- Tests must be independent and reproducible

### Documentation Requirements

- Public APIs must have docstrings
- New features must update user documentation
- Breaking changes must be explained in CHANGELOG

---

## Code Review Process

### Review Criteria

1. **Functionality** - Does the code work as expected
2. **Code quality** - Does it follow code standards
3. **Test coverage** - Is there adequate testing
4. **Documentation** - Is relevant documentation updated
5. **Performance impact** - Is there performance degradation

### Review Process

1. **Automated checks** - CI/CD runs tests and checks automatically
2. **Maintainer review** - At least 1 maintainer reviews
3. **Feedback and revision** - Revise code based on review comments
4. **Merge** - Merge to main branch after approval

### Review Timeline

- We try to respond within **48 hours**
- Complex PRs may take longer
- Please be patient, thank you for understanding

---

## Release Process

### Version Naming

Uses [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH
  │     │     │
  │     │     └─ Backward compatible bug fixes
  │     └─────── Backward compatible new features
  └───────────── Incompatible API changes
```

### Release Cycle

- **PATCH** - As needed (bug fixes)
- **MINOR** - Monthly (new features)
- **MAJOR** - Quarterly (major updates)

### Release Steps

1. Create release branch
2. Update version and CHANGELOG
3. Create Release Candidate
4. Community testing and voting (72 hours)
5. Official release after vote passes
6. Publish to PyPI
7. Create GitHub Release

See [RELEASE.md](docs/RELEASE.md) for detailed process.

---

## Frequently Asked Questions

### Q: How long until my PR is reviewed?

A: We try to respond within 48 hours. If no response after a week, you can @maintainers to remind.

### Q: Can I submit partially completed features?

A: Yes! Please use Draft PR and explain the completion status in the description.

### Q: How do I become a maintainer?

A: Continuous contribution, active community participation, helping other contributors. Maintainers will invite active contributors to join.

### Q: What if my code style is not accepted?

A: Please follow the project's code standards. If you have different opinions, you can discuss in Issues.

---

## Acknowledgments

Thank you to everyone who has contributed to claw-mem!

<a href="https://github.com/yourusername/claw-mem/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=yourusername/claw-mem" />
</a>

---

**Happy Contributing! 🚀**
