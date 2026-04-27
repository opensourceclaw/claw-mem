# 🚀 claw-mem ClawHub Publishing Guide

> Created: 2026-04-17
> Project: `/Users/liantian/workspace/osprojects/claw-mem`
> Skill Location: `skill/`

---

## ✅ Completed

### 1. Skill Structure Created

```
claw-mem/
├── skill/
│   ├── SKILL.md                    ✅ Usage guide + triggers
│   ├── scripts/
│   │   ├── search.py               ✅ Search memory
│   │   ├── store.py                ✅ Store memory
│   │   └── bridge.py               ✅ Start JSON-RPC Bridge
│   └── references/
│       ├── architecture.md         ✅ Three-tier architecture
│       └── retrieval.md            ✅ Retrieval algorithms
├── src/claw_mem/                   # Python core code
├── claw_mem_plugin/                # TypeScript OpenClaw plugin
└── pyproject.toml                  # Python package config
```

### 2. Scripts Tested

```bash
$ python3 skill/scripts/search.py --help
usage: search.py [-h] [--limit LIMIT] [--mode MODE] query

$ python3 skill/scripts/store.py --help
usage: store.py [-h] [--category CATEGORY] [--layer LAYER] text
```

---

## 📋 Publishing Steps

### Step 1: Login to ClawHub

```bash
npx clawhub@latest login
```

This opens a browser for GitHub OAuth authorization.

### Step 2: Verify Login

```bash
npx clawhub@latest whoami
```

Expected output:
```
Logged in as <your-github-username>
```

### Step 3: Publish Skill

```bash
cd /Users/liantian/workspace/osprojects/claw-mem

npx clawhub@latest publish ./skill \
  --slug claw-mem \
  --name "claw-mem: Three-Tier Memory" \
  --version 2.0.0 \
  --tags "memory,ai,openclaw,latest"
```

### Step 4: Verify Publication

```bash
npx clawhub@latest inspect claw-mem
```

Expected output:
```
claw-mem  claw-mem: Three-Tier Memory
Summary: Three-Tier Memory System for OpenClaw agents...
Owner: <your-github-username>
Latest: 2.0.0
Tags: memory=2.0.0, ai=2.0.0, openclaw=2.0.0, latest=2.0.0
```

---

## 🔧 Post-Publication

### User Installation

```bash
# Install Python package
pip install claw-mem

# Install Skill
npx clawhub@latest install claw-mem
```

### User Usage

```bash
# Search memory
python3 ~/.openclaw/workspace/skills/claw-mem/scripts/search.py "project"

# Store memory
python3 ~/.openclaw/workspace/skills/claw-mem/scripts/store.py "Important fact"
```

---

## 📊 ClawHub CLI Reference

| Command | Description |
|---------|-------------|
| `npx clawhub@latest login` | Login |
| `npx clawhub@latest whoami` | Verify login |
| `npx clawhub@latest publish <path>` | Publish skill |
| `npx clawhub@latest inspect <slug>` | View details |
| `npx clawhub@latest search <query>` | Search skills |
| `npx clawhub@latest install <slug>` | Install skill |
| `npx clawhub@latest update <slug>` | Update skill |
| `npx clawhub@latest list` | List installed |

---

## 🔄 Version Update Process

### Update Skill

```bash
cd /Users/liantian/workspace/osprojects/claw-mem

# After modifying files in skill/
npx clawhub@latest publish ./skill \
  --slug claw-mem \
  --version 2.1.0 \
  --changelog "Added vector search support"
```

### Update Python Package

```bash
cd /Users/liantian/workspace/osprojects/claw-mem
pip install -e .
```

---

## 🎯 Solution Summary

### Adopted Approach: Hybrid Plugin + Skill

**Architecture:**
```
User → ClawHub Skill → claw-mem Python Package → SQLite Storage
```

**Advantages:**
1. ✅ Maintains Python package independence
2. ✅ Skill as lightweight entry point
3. ✅ Independent updates possible
4. ✅ Follows ClawHub design principles

**Dependencies:**
- **Skill** → Published to ClawHub.ai
- **Python Package** → Published to PyPI (`pip install claw-mem`)
- **OpenClaw Plugin** → Published to npm (`@opensourceclaw/openclaw-claw-mem`)

---

## 📝 Related Documentation

- Detailed Plan: `docs/clawhub-publish-plan.md`
- Comparison Analysis: `docs/claude-mem-comparison.md`
- Skill Location: `skill/`

---

**Next Step**: Execute Steps 1-4 to complete ClawHub publication
