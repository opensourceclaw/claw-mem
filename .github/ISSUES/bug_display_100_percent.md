---
name: 🐛 Bug Report
about: Create a report to help us improve
title: '[BUG] Display inconsistency: "100%" sometimes shown as "10%"'
labels: bug, display, priority-medium
---

## Describe the Bug

The release process rule "Release Notes 100% English" sometimes displays as "10% English" in assistant responses, even though the source file is correct.

## Source File Content

The file `memory/releases/claw-mem-release-process.md` correctly contains:
```markdown
3. **Release Notes**: 
   - 100% 英文，不提及 AI 贡献者
```

## Expected Behavior

Always display "100% 英文" (100% English)

## Actual Behavior

Sometimes displays as "10% 英文" in assistant responses

## Possible Causes

1. Tokenization issue with "100%"
2. Display/rendering bug
3. Memory retrieval issue

## Impact

- Confusing for users
- Appears unprofessional
- Requires multiple corrections

## Proposed Fix for v0.7.0

1. Investigate tokenization of percentage values
2. Add validation for release process rules
3. Implement display consistency checks

## Workaround

Manually verify the source file content when in doubt.

## Environment

- Version: v0.6.0
- OS: macOS
- Python: 3.14
