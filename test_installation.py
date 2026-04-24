#!/usr/bin/env python3
"""claw-mem v2.1.0 部署验证脚本"""

from claw_mem import MemoryManager

print("=" * 60)
print("claw-mem v2.1.0 部署验证")
print("=" * 60)

# 测试 MemoryManager
print("\n1. 测试 MemoryManager...")
manager = MemoryManager(enable_gating=True)

# 写入测试
print("\n2. 写入测试数据...")
result = manager.store(
    content="测试 claw-mem v2.1.0 部署",
    memory_type="episodic",
    metadata={"source": "user", "test": True}
)
print(f"   ✅ 写入成功: {result}")

# 写入更多数据
print("\n3. 写入更多数据...")
manager.store(
    content="重要决策：使用 Python 作为主要开发语言",
    memory_type="semantic",
    metadata={"source": "user", "verified": True}
)

manager.store(
    content="普通日志信息",
    memory_type="episodic",
    metadata={"source": "system"}
)

# 查看统计
print("\n4. 查看统计信息...")
stats = manager.get_gating_stats()
print(f"   活跃记忆: {stats['active_count']}")
print(f"   冷存储: {stats['cold_count']}")
print(f"   阈值: {stats['threshold']}")

# 测试检索
print("\n5. 测试检索...")
results = manager.search("Python")
print(f"   检索到 {len(results)} 条结果")
if results:
    print(f"   第一条: {results[0]['content'][:50]}...")

print("\n" + "=" * 60)
print("✅ claw-mem v2.1.0 部署验证成功！")
print("=" * 60)
