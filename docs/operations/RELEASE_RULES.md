# Release Rules - 项目发布规范

**Effective Date:** 2026-03-25  
**Applies To:** NeoClaw, claw-mem, claw-rl  
**Status:** ✅ Active

---

## 📋 GitHub Release 规范

### Release Title 格式

**规则：** `项目名称 vx.x.x`

**示例：**
- ✅ `claw-mem v1.0.5`
- ✅ `claw-rl v0.6.0`
- ✅ `NeoClaw v0.6.0`
- ❌ `claw-mem v1.0.5: Metadata Support` (不要描述)
- ❌ `NeoClaw v0.6.0 - Service Layer` (不要描述)

**说明：**
- Title 仅包含项目名称和版本号
- 不要有任何额外描述
- 描述内容放在 Release Notes (body) 中

---

### Release Notes 格式

```markdown
## ✨ New Features

- Feature 1
- Feature 2

## 🔧 Technical Details

- Detail 1
- Detail 2

## 📦 Installation
command here

## 🧪 Testing
Test info here

**Full Changelog:** [link]
```

---

## 🚫 不包含的流程

### 不包含 PyPI 上传

**规则：** Python 项目不上传 PyPI

**说明：**
- 仅发布 GitHub Release
- 不上传到 PyPI
- 用户通过 GitHub 安装

**安装方式：**
```bash
# 从 GitHub 安装
pip install git+https://github.com/opensourceclaw/claw-mem.git@v1.0.5

# 或克隆后本地安装
git clone https://github.com/opensourceclaw/claw-mem.git
cd claw-mem
pip install -e .
```

---

## 📦 发布流程

### 标准发布流程

```bash
# 1. 更新版本号
# 编辑 pyproject.toml: version = "x.x.x"

# 2. Git 提交
git add <files>
git commit -m "feat: Description (vx.x.x)"

# 3. 推送代码
git push origin main

# 4. 创建 Git Tag
git tag -a vx.x.x -m "Project Name vx.x.x"
git push origin vx.x.x

# 5. 创建 GitHub Release
gh release create vx.x.x \
  --title "Project Name vx.x.x" \
  --notes "Release notes here"

# 6. 验证
gh release view vx.x.x
```

---

## 🎯 版本命名规范

### Semantic Versioning

格式：`主版本号。次版本号。修订号`

| 变更类型 | 版本更新 | 示例 |
|---------|---------|------|
| **Breaking Changes** | 主版本号 +1 | v1.0.0 → v2.0.0 |
| **新功能 (向后兼容)** | 次版本号 +1 | v1.0.4 → v1.0.5 |
| **Bug 修复** | 修订号 +1 | v1.0.4 → v1.0.5 |

### 项目当前版本

| 项目 | 当前版本 | 下一版本 |
|------|---------|---------|
| **claw-mem** | v1.0.5 | v1.1.0 |
| **claw-rl** | v0.6.0 | v0.7.0 |
| **NeoClaw** | v0.6.0 | v0.7.0 |

---

## 📝 Commit Message 规范

### 格式

```
<type>: <description> (version)

[optional body]

[optional footer]
```

### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: Add metadata support (v1.0.5)` |
| `fix` | Bug 修复 | `fix: Fix search filtering (v1.0.4)` |
| `docs` | 文档更新 | `docs: Update README (v1.0.5)` |
| `test` | 测试更新 | `test: Add metadata tests (v1.0.5)` |
| `refactor` | 代码重构 | `refactor: Simplify API (v1.1.0)` |

### 示例

```bash
# 新功能
git commit -m "feat: Add metadata support for NeoClaw integration (v1.0.5)"

# Bug 修复
git commit -m "fix: Fix metadata filtering edge case (v1.0.5)"

# 文档更新
git commit -m "docs: Add release rules documentation (v1.0.5)"
```

---

## 🔖 Tag 规范

### Git Tag 格式

```bash
# 创建 Tag
git tag -a vx.x.x -m "Project Name vx.x.x"

# 推送 Tag
git push origin vx.x.x
```

### Tag Message 格式

```
Project Name vx.x.x

Release Date: YYYY-MM-DD
Type: Patch/Minor/Major Release

Brief description of changes.
```

---

## ✅ 发布检查清单

### 发布前

- [ ] 版本号已更新 (pyproject.toml)
- [ ] 代码已提交并推送
- [ ] 测试已通过
- [ ] Release Notes 已准备
- [ ] Git Tag 已创建

### 发布后

- [ ] GitHub Release 已创建
- [ ] Release Title 格式正确
- [ ] Release Notes 完整
- [ ] 链接验证有效
- [ ] 社区公告已发布

---

## 📚 参考文档

- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)

---

**Document Status:** ✅ Active  
**Last Updated:** 2026-03-25  
**Next Review:** 2026-06-25
