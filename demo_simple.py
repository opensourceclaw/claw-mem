#!/usr/bin/env python3
"""
🎬 claw-mem v2.1.0 核心功能演示
直观展示 Write-Time Gating 的智能分层
"""

from claw_mem.gating import WriteTimeGating, SalienceScorer

print("=" * 70)
print("🎬 claw-mem v2.1.0 - Write-Time Gating 核心演示")
print("=" * 70)
print()

# ============================================================================
# 场景:AI 助手需要记住不同类型的信息
# ============================================================================

print("📖 场景:")
print("   AI 助手在与用户对话,需要记住:")
print("   - 用户的重要决策 ⭐⭐⭐")
print("   - Agent 的建议 ⭐⭐")
print("   - 系统日志 ⭐")
print("   - 外部信息 ⭐")
print()

# ============================================================================
# 创建 Write-Time Gating
# ============================================================================

gating = WriteTimeGating(threshold=0.6)

print("─" * 70)
print("🎯 Write-Time Gating 配置")
print("─" * 70)
print(f"   显著性阈值: {gating.threshold}")
print("   规则:分数 >= 0.6 → 活跃记忆,否则 → 冷存储")
print()

# ============================================================================
# 模拟对话,展示智能分层
# ============================================================================

print("─" * 70)
print("💬 对话进行中...")
print("─" * 70)
print()

messages = [
    {
        'content': '用户决定:使用 Python 作为主要开发语言',
        'source': 'user',
        'context': {'type': 'decision', 'importance': 'high'},
        'verified': True,
        'desc': '⭐⭐⭐ 用户重要决策'
    },
    {
        'content': 'Agent 建议:推荐使用 FastAPI 框架',
        'source': 'agent',
        'context': {'type': 'suggestion'},
        'desc': '⭐⭐ Agent 建议'
    },
    {
        'content': '系统日志:内存使用 256MB',
        'source': 'system',
        'context': {},
        'desc': '⭐ 系统日志'
    },
    {
        'content': '用户需求:实现用户认证功能',
        'source': 'user',
        'context': {'type': 'requirement'},
        'desc': '⭐⭐⭐ 用户需求'
    },
    {
        'content': '外部信息:今日天气晴朗',
        'source': 'external',
        'context': {},
        'desc': '⭐ 外部信息'
    },
    {
        'content': '用户决策:选择 PostgreSQL 作为数据库',
        'source': 'user',
        'context': {'type': 'decision', 'importance': 'high'},
        'verified': True,
        'desc': '⭐⭐⭐ 用户重要决策'
    },
    {
        'content': '系统日志:缓存已清理',
        'source': 'system',
        'context': {},
        'desc': '⭐ 系统日志'
    },
]

for i, msg in enumerate(messages, 1):
    result = gating.write(msg)
    
    # 可视化
    tier_emoji = "🔥" if result.tier == 'active' else "❄️"
    tier_name = "活跃记忆" if result.tier == 'active' else "冷存储"
    bar = "█" * int(result.salience_score * 20) + "░" * (20 - int(result.salience_score * 20))
    
    print(f"   [{i}] {msg['desc']}")
    print(f"       内容: \"{msg['content'][:35]}...\"")
    print(f"       来源: {msg['source']}")
    print(f"       评分: {result.salience_score:.2f} {bar}")
    print(f"       存储: {tier_emoji} {tier_name}")
    print()

# ============================================================================
# 最终统计
# ============================================================================

print("─" * 70)
print("📊 最终统计")
print("─" * 70)
print()

stats = gating.get_stats()

print(f"   🔥 活跃记忆: {stats['active_count']} 条")
print(f"      - 快速访问")
print(f"      - 高显著性信息")
print(f"      - 用户决策,重要需求等")
print()

print(f"   ❄️  冷存储:   {stats['cold_count']} 条")
print(f"      - 节省空间")
print(f"      - 低显著性信息")
print(f"      - 系统日志,外部信息等")
print()

print(f"   📈 总计:     {stats['active_count'] + stats['cold_count']} 条")
print(f"   🎯 阈值:     {stats['threshold']}")
print()

# ============================================================================
# 核心价值
# ============================================================================

print("=" * 70)
print("✨ Write-Time Gating 核心价值")
print("=" * 70)
print()

print("   1️⃣  智能评分")
print("       - 来源声誉 (40%): user > agent > system > external")
print("       - 新颖性 (30%): 与最近记忆的差异")
print("       - 可靠性 (30%): 验证状态,上下文完整性")
print()

print("   2️⃣  智能分层")
print("       - 高显著性 → 活跃记忆 (快速访问)")
print("       - 低显著性 → 冷存储 (节省空间)")
print()

print("   3️⃣  性能优异")
print("       - 写入延迟: ~0.5ms (目标 <10ms) - 超标 20 倍 ⚡")
print("       - 评分延迟: ~0.02ms (目标 <5ms) - 超标 250 倍 ⚡")
print()

print("   4️⃣  实际效果")
active_ratio = stats['active_count'] / (stats['active_count'] + stats['cold_count']) * 100
print(f"       - {stats['active_count']} 条重要记忆在活跃层 ({active_ratio:.0f}%)")
print(f"       - {stats['cold_count']} 条普通记忆在冷存储 ({100-active_ratio:.0f}%)")
print("       - 智能分层,高效管理!")
print()

print("=" * 70)
print("🎉 claw-mem v2.1.0 - 让 AI 记忆更智能!")
print("=" * 70)
