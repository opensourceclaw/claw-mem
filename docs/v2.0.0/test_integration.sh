#!/bin/bash
# Project Neo 三系统联动测试
# neoclaw v2.0.0-beta + claw-mem v2.0.0-beta + claw-rl v2.0.0-beta.1

echo "========================================"
echo "Project Neo 三系统联动测试"
echo "========================================"
echo ""

# 1. 检查版本
echo "1. 版本检查"
echo "----------------------------------------"
echo "neoclaw:    $(cd /Users/liantian/workspace/osprojects/neoclaw 2>/dev/null && git describe --tags 2>/dev/null || echo '未发布')"
echo "claw-mem:   $(cd /Users/liantian/workspace/osprojects/claw-mem 2>/dev/null && git describe --tags 2>/dev/null || echo '未发布')"
echo "claw-rl:    $(cd /Users/liantian/workspace/osprojects/claw-rl 2>/dev/null && git describe --tags 2>/dev/null || echo '未发布')"
echo ""

# 2. 检查 Plugin 安装
echo "2. Plugin 安装状态"
echo "----------------------------------------"
if [ -d "/Users/liantian/workspace/osprojects/claw-mem/claw_mem_plugin" ]; then
    echo "✅ claw-mem Plugin 目录存在"
else
    echo "❌ claw-mem Plugin 目录不存在"
fi

if [ -d "/Users/liantian/workspace/osprojects/claw-rl/claw_rl_plugin" ]; then
    echo "✅ claw-rl Plugin 目录存在"
else
    echo "❌ claw-rl Plugin 目录不存在"
fi
echo ""

# 3. 检查 Bridge 可用性
echo "3. Bridge 可用性检查"
echo "----------------------------------------"
echo "claw-mem Bridge:"
cd /Users/liantian/workspace/osprojects/claw-mem 2>/dev/null
if [ -f "src/claw_mem/bridge.py" ]; then
    source venv/bin/activate 2>/dev/null
    python3 -c "from claw_mem.bridge import ClawMemBridge; print('  ✅ 导入成功')" 2>&1
else
    echo "  ❌ Bridge 文件不存在"
fi

echo "claw-rl Bridge:"
cd /Users/liantian/workspace/osprojects/claw-rl 2>/dev/null
if [ -f "src/claw_rl/bridge.py" ]; then
    source venv/bin/activate 2>/dev/null
    python3 -c "from claw_rl.bridge import ClawRLBridge; print('  ✅ 导入成功')" 2>&1
else
    echo "  ❌ Bridge 文件不存在"
fi
echo ""

# 4. 检查 OpenClaw 配置
echo "4. OpenClaw 配置检查"
echo "----------------------------------------"
if [ -f "$HOME/.openclaw/openclaw.json" ]; then
    echo "✅ OpenClaw 配置文件存在"
    
    # 检查 claw-mem
    if grep -q '"claw-mem"' "$HOME/.openclaw/openclaw.json" 2>/dev/null; then
        echo "✅ claw-mem 已配置"
    else
        echo "⚠️  claw-mem 未配置"
    fi
    
    # 检查 claw-rl
    if grep -q '"claw-rl"' "$HOME/.openclaw/openclaw.json" 2>/dev/null; then
        echo "✅ claw-rl 已配置"
    else
        echo "⚠️  claw-rl 未配置"
    fi
else
    echo "❌ OpenClaw 配置文件不存在"
fi
echo ""

# 5. 测试 claw-rl 功能
echo "5. claw-rl 功能测试"
echo "----------------------------------------"
cd /Users/liantian/workspace/osprojects/claw-rl 2>/dev/null
if [ -f "claw_rl_plugin/test/test_integration.js" ]; then
    echo "运行集成测试..."
    cd claw_rl_plugin
    node test/test_integration.js 2>&1 | grep -E "Test|✅|Total" | head -10
else
    echo "⚠️  集成测试文件不存在"
fi
echo ""

# 6. 总结
echo "========================================"
echo "联动测试总结"
echo "========================================"
echo "✅ 所有检查完成"
echo ""
echo "建议："
echo "1. 确保 OpenClaw Gateway 正在运行"
echo "2. 使用 'openclaw plugins list' 检查 Plugin 加载状态"
echo "3. 测试 Tools: learning_status, memory_search"
echo "4. 观察 OpenClaw 日志: openclaw logs --follow"
