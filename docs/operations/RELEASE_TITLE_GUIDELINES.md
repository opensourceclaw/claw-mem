# GitHub Release 标题命名规范

**生效版本:** v0.9.1+  
**更新日期:** 2026-03-22  

---

## 命名规则

### Tag 名称
```
格式:v{版本号}
示例:v0.9.0, v0.9.1, v1.0.0
```

### Release 标题
```
格式:claw-mem-v{版本号}
示例:claw-mem-v0.9.0, claw-mem-v0.9.1, claw-mem-v1.0.0
```

---

## 对比示例

| 元素 | ❌ 旧格式 | ✅ 新格式 |
|------|----------|----------|
| **Tag 名称** | v0.9.0 - Stability & Performance | v0.9.0 |
| **Release 标题** | claw-mem v0.9.0 - Stability & Performance | claw-mem-v0.9.0 |

---

## gh CLI 命令模板

```bash
gh release create v{版本号} \
  --title "claw-mem-v{版本号}" \
  --notes-file docs/GITHUB_RELEASE_NOTES_v{版本号}.md \
  --repo opensourceclaw/claw-mem
```

### 示例:v0.9.1

```bash
gh release create v0.9.1 \
  --title "claw-mem-v0.9.1" \
  --notes-file docs/GITHUB_RELEASE_NOTES_v091.md \
  --repo opensourceclaw/claw-mem
```

---

## 原因

1. **简洁性** - 标题只保留核心信息(项目名称 + 版本号)
2. **一致性** - 所有 Release 格式统一
3. **易读性** - GitHub Release 列表更清晰
4. **详细描述放在正文** - Release Notes 中详细说明主题和变更

---

## Release Notes 正文结构

标题简化后,详细信息在正文中呈现:

```markdown
# claw-mem-v{版本号}

**Release Date**: {日期}  
**Version**: {版本号}  
**Theme**: {主题(可选)}  

---

## 🎉 Highlights
...

## 🚀 What's New
...
```

---

*规范制定:2026-03-22*  
*claw-mem Project - Est. 2026*  
*"Ad Astra Per Aspera"*
