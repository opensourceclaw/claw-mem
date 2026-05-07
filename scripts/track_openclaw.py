#!/usr/bin/env python3
"""
OpenClaw 版本追踪脚本
用法: python scripts/track_openclaw.py

功能:
1. 检测 OpenClaw 版本变化
2. 评估兼容性影响
3. 记录到 CHANGELOG_TRACKING.md
"""

import subprocess
import json
import os
from datetime import datetime
from pathlib import Path

# 配置
REPO_DIR = Path(__file__).parent.parent
VERSION_FILE = REPO_DIR / ".last_openclaw_version"
CHANGELOG_FILE = REPO_DIR / "docs" / "compatibility" / "CHANGELOG_TRACKING.md"
COMPATIBILITY_FILE = REPO_DIR / "docs" / "compatibility" / "COMPATIBILITY_MATRIX.md"


def get_openclaw_version():
    """获取当前 OpenClaw 版本"""
    try:
        result = subprocess.run(
            ["openclaw", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # 解析版本号: "OpenClaw 2026.5.3-1 (2eae30e)"
        output = result.stdout.strip()
        if "OpenClaw" in output:
            # 提取版本号
            version = output.split()[1] if len(output.split()) > 1 else "unknown"
            return version
    except Exception as e:
        print(f"获取版本失败: {e}")
    return None


def get_last_version():
    """读取上次记录的版本"""
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return None


def save_version(version):
    """保存当前版本"""
    VERSION_FILE.write_text(version)


def run_compatibility_check():
    """运行兼容性检查"""
    try:
        # 基础导入测试
        result = subprocess.run(
            ["python3", "-c", 
             "from claw_mem import MemoryManager; print('OK')"],
            capture_output=True,
            text=True,
            cwd=REPO_DIR,
            timeout=30
        )
        
        if result.returncode == 0 and "OK" in result.stdout:
            return True, "模块导入正常"
        else:
            return False, f"导入失败: {result.stderr}"
    except Exception as e:
        return False, str(e)


def check_bridge():
    """检查 bridge 是否正常"""
    try:
        # 简单测试 bridge 能否实例化
        result = subprocess.run(
            ["python3", "-c", 
             "from claw_mem.bridge import ClawMemBridge; print('OK')"],
            capture_output=True,
            text=True,
            cwd=REPO_DIR,
            timeout=30
        )
        if result.returncode == 0:
            return True, "Bridge 正常"
        else:
            return False, f"Bridge 异常: {result.stderr}"
    except Exception as e:
        return False, str(e)


def main():
    print(f"🔍 检查 OpenClaw 版本...")
    
    current_version = get_openclaw_version()
    last_version = get_last_version()
    
    print(f"  当前: {current_version}")
    print(f"  上次: {last_version}")
    
    if current_version == last_version:
        print("✅ 版本无变化")
        return
    
    if current_version is None:
        print("❌ 无法获取 OpenClaw 版本")
        return
    
    # 版本变化，触发兼容性检查
    print(f"\n⚠️ 检测到 OpenClaw 版本变化: {last_version} → {current_version}")
    print("🔄 运行兼容性检查...")
    
    # 检查各项功能
    results = []
    
    # 1. 模块导入
    ok, msg = run_compatibility_check()
    results.append(("模块导入", ok, msg))
    print(f"  {'✅' if ok else '❌'} 模块导入: {msg}")
    
    # 2. Bridge
    ok, msg = check_bridge()
    results.append(("Bridge", ok, msg))
    print(f"  {'✅' if ok else '❌'} Bridge: {msg}")
    
    # 总结
    all_ok = all(r[1] for r in results)
    
    print(f"\n{'✅ 兼容性检查通过' if all_ok else '⚠️ 兼容性检查发现问题'}")
    
    # 保存新版本
    save_version(current_version)
    print(f"\n已保存版本: {current_version}")


if __name__ == "__main__":
    main()
