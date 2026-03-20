#!/usr/bin/env python3
"""
claw-mem Auto Configuration Detection

Automatically detects OpenClaw workspace path.
"""

import os
from pathlib import Path
from typing import Optional, List

from .errors import WorkspaceNotFoundError


class ConfigDetector:
    """自动检测 OpenClaw 配置"""
    
    # 默认搜索路径（按优先级排序）
    DEFAULT_PATHS = [
        # 标准 OpenClaw 路径
        os.path.expanduser("~/.openclaw/workspace"),
        os.path.expanduser("~/.config/openclaw/workspace"),
        
        # 当前目录（如果是工作区）
        os.getcwd(),
        
        # 其他常见路径
        os.path.expanduser("~/workspace"),
        os.path.expanduser("~/projects"),
    ]
    
    # 工作区特征文件/目录
    WORKSPACE_MARKERS = [
        "MEMORY.md",           # 核心记忆文件
        "memory/",             # 记忆目录
        "AGENTS.md",           # Agent 配置
        "SOUL.md",             # 人格配置
        "USER.md",             # 用户配置
    ]
    
    @classmethod
    def detect_workspace(cls, custom_paths: Optional[List[str]] = None) -> str:
        """
        检测 OpenClaw workspace 路径
        
        Args:
            custom_paths: 自定义搜索路径列表（可选）
        
        Returns:
            str: 检测到的 workspace 路径
        
        Raises:
            WorkspaceNotFoundError: 如果未找到有效的工作区
        """
        # 合并路径列表
        search_paths = custom_paths if custom_paths else cls.DEFAULT_PATHS
        
        # 记录已搜索的路径
        searched_paths = []
        
        # 遍历所有路径
        for path_str in search_paths:
            path = Path(path_str).expanduser().resolve()
            searched_paths.append(str(path))
            
            # 检查路径是否存在
            if not path.exists():
                continue
            
            # 检查是否是有效的工作区
            if cls._is_valid_workspace(path):
                return str(path)
        
        # 未找到，抛出友好错误
        raise WorkspaceNotFoundError(searched_paths)
    
    @classmethod
    def _is_valid_workspace(cls, path: Path) -> bool:
        """
        验证路径是否是有效的 OpenClaw workspace
        
        Args:
            path: 待验证的路径
        
        Returns:
            bool: 是否是有效的工作区
        """
        # 至少需要一个特征文件或目录
        for marker in cls.WORKSPACE_MARKERS:
            marker_path = path / marker
            
            # 检查文件或目录是否存在
            if marker_path.exists():
                # 额外验证：如果是目录，检查是否为空
                if marker_path.is_dir():
                    # 目录不为空才有效
                    if any(marker_path.iterdir()):
                        return True
                else:
                    # 文件存在即有效
                    return True
        
        # 没有找到任何特征
        return False
    
    @classmethod
    def get_workspace_info(cls, workspace_path: str) -> dict:
        """
        获取工作区详细信息
        
        Args:
            workspace_path: 工作区路径
        
        Returns:
            dict: 工作区信息
        """
        path = Path(workspace_path).expanduser().resolve()
        
        info = {
            "path": str(path),
            "exists": path.exists(),
            "is_valid": cls._is_valid_workspace(path) if path.exists() else False,
            "markers_found": [],
            "memory_files": [],
        }
        
        if not path.exists():
            return info
        
        # 检查特征文件
        for marker in cls.WORKSPACE_MARKERS:
            marker_path = path / marker
            if marker_path.exists():
                info["markers_found"].append(marker)
        
        # 检查记忆文件
        memory_dir = path / "memory"
        if memory_dir.exists() and memory_dir.is_dir():
            md_files = list(memory_dir.glob("*.md"))
            info["memory_files"] = [f.name for f in md_files[:10]]  # 最多 10 个
        
        return info
    
    @classmethod
    def suggest_workspace(cls) -> Optional[str]:
        """
        建议一个工作区路径（如果不存在则创建）
        
        Returns:
            Optional[str]: 建议的路径，如果无法创建则返回 None
        """
        # 首选路径
        preferred = Path("~/.openclaw/workspace").expanduser()
        
        # 如果已存在，直接返回
        if cls._is_valid_workspace(preferred):
            return str(preferred)
        
        # 尝试创建
        try:
            preferred.mkdir(parents=True, exist_ok=True)
            return str(preferred)
        except (OSError, PermissionError):
            # 创建失败
            return None


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 示例 1：自动检测
    try:
        workspace = ConfigDetector.detect_workspace()
        print(f"✅ 检测到工作区：{workspace}")
    except WorkspaceNotFoundError as e:
        print(e)
    
    print()
    
    # 示例 2：获取工作区信息
    try:
        workspace = ConfigDetector.detect_workspace()
        info = ConfigDetector.get_workspace_info(workspace)
        
        print("工作区信息:")
        print(f"  路径：{info['path']}")
        print(f"  存在：{info['exists']}")
        print(f"  有效：{info['is_valid']}")
        print(f"  特征文件：{', '.join(info['markers_found'])}")
        print(f"  记忆文件：{', '.join(info['memory_files'][:5])}")
    except WorkspaceNotFoundError:
        print("未找到工作区，无法获取信息")
    
    print()
    
    # 示例 3：建议工作区
    suggested = ConfigDetector.suggest_workspace()
    if suggested:
        print(f"💡 建议的工作区：{suggested}")
    else:
        print("❌ 无法创建建议的工作区")
