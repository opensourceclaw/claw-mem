# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

---

## 📚 经验教训（从 Agent-Memory 迁移）

### 技能安装
- ⚠️ **ClawHub 速率限制**：安装技能有速率限制，失败后等待 5-10 分钟再试
- ✅ **最佳实践**：Friday 负责任务指挥，Claude Code 负责编码执行，组合使用效果最佳

### 系统兼容
- ⚠️ **macOS 版本**：macOS 11 (Big Sur) 太旧，gh CLI 依赖的 go 需要 macOS 12+

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- （暂无配置）
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
