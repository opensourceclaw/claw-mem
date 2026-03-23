#!/usr/bin/env python3
# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
claw-mem Auto Configuration Detection

Automatically detects OpenClaw workspace path.
"""

import os
from pathlib import Path
from typing import Optional, List

from .errors import WorkspaceNotFoundError


class ConfigDetector:
    """Auto-detect OpenClaw configuration"""
    
    # Default search paths (sorted by priority)
    DEFAULT_PATHS = [
        # Standard OpenClaw paths
        os.path.expanduser("~/.openclaw/workspace"),
        os.path.expanduser("~/.config/openclaw/workspace"),
        
        # Current directory (if workspace)
        os.getcwd(),
        
        # Other common paths
        os.path.expanduser("~/workspace"),
        os.path.expanduser("~/projects"),
    ]
    
    # Workspace marker files/directories
    WORKSPACE_MARKERS = [
        "MEMORY.md",           # Core memory file
        "memory/",             # Memory directory
        "AGENTS.md",           # Agent configuration
        "SOUL.md",             # Personality configuration
        "USER.md",             # User configuration
    ]
    
    @classmethod
    def detect_workspace(cls, custom_paths: Optional[List[str]] = None) -> str:
        """
        Detect OpenClaw workspace path
        
        Args:
            custom_paths: Custom search paths list (optional)
        
        Returns:
            str: Detected workspace path
        
        Raises:
            WorkspaceNotFoundError: 如果未找到有效的工作区
        """
        # 合并路径列表
        search_paths = custom_paths if custom_paths else cls.DEFAULT_PATHS
        
        # Record searched paths
        searched_paths = []
        
        # Iterate through all paths
        for path_str in search_paths:
            path = Path(path_str).expanduser().resolve()
            searched_paths.append(str(path))
            
            # Check if path exists
            if not path.exists():
                continue
            
            # Check if valid workspace
            if cls._is_valid_workspace(path):
                return str(path)
        
        # Not found, raise friendly error
        raise WorkspaceNotFoundError(searched_paths)
    
    @classmethod
    def _is_valid_workspace(cls, path: Path) -> bool:
        """
        Validate if path is valid OpenClaw workspace
        
        Args:
            path: Path to validate
        
        Returns:
            bool: Whether valid workspace
        """
        # At least one marker file/directory needed
        for marker in cls.WORKSPACE_MARKERS:
            marker_path = path / marker
            
            # Check if file/directory exists
            if marker_path.exists():
                # Extra validation: if directory, check if not empty
                if marker_path.is_dir():
                    # Directory must not be empty to be valid
                    if any(marker_path.iterdir()):
                        return True
                else:
                    # File existence is sufficient
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
