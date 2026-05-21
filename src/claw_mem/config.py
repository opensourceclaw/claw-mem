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
from typing import Any, List, Optional

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
        "MEMORY.md",  # Core memory file
        "memory/",  # Memory directory
        "AGENTS.md",  # Agent configuration
        "SOUL.md",  # Personality configuration
        "USER.md",  # User configuration
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
            WorkspaceNotFoundError: if no valid workspace found
        """
        # Merge path list
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

        # No features found
        return False

    @classmethod
    def get_workspace_info(cls, workspace_path: str) -> dict:
        """
        Get workspace details

        Args:
            workspace_path: workspace path

        Returns:
            dict: workspace info
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

        # Check feature files
        for marker in cls.WORKSPACE_MARKERS:
            marker_path = path / marker
            if marker_path.exists():
                info["markers_found"].append(marker)

        # Check memory files
        memory_dir = path / "memory"
        if memory_dir.exists() and memory_dir.is_dir():
            md_files = list(memory_dir.glob("*.md"))
            info["memory_files"] = [f.name for f in md_files[:10]]  # Max 10

        return info

    @classmethod
    def suggest_workspace(cls) -> Optional[str]:
        """
        Suggest a workspace path (create if not exists)

        Returns:
            Optional[str]: suggested path, or None if cannot create
        """
        # Preferred path
        preferred = Path("~/.openclaw/workspace").expanduser()

        # If exists, return directly
        if cls._is_valid_workspace(preferred):
            return str(preferred)

        # Try to create
        try:
            preferred.mkdir(parents=True, exist_ok=True)
            return str(preferred)
        except (OSError, PermissionError):
            # Create failed
            return None


# ============================================================================
# Memory Configuration
# ============================================================================


class MemoryConfig:
    """Configuration for MemoryManager.

    Encapsulates all MemoryManager initialization parameters in a single
    dataclass-style object for cleaner API. Replaces the 32-parameter
    __init__ with a single config parameter.

    Usage:
        # Default config with workspace
        config = MemoryConfig(workspace="/path/to/workspace")

        # Custom retrieval config
        config = MemoryConfig(
            workspace="/path/to/workspace",
            enable_gating=True,
            gating_threshold=0.8,
            bm25_weight=0.6,
        )

        mm = MemoryManager(config=config)
    """

    def __init__(
        self,
        # Workspace
        workspace: Optional[str] = None,
        auto_detect: bool = True,
        # Retrieval
        bm25_k1: float = 1.5,
        bm25_b: float = 0.75,
        bm25_weight: float = 0.7,
        keyword_weight: float = 0.3,
        recency_boost: float = 1.0,
        frequency_boost: float = 1.0,
        # Features
        enable_gating: bool = False,
        gating_threshold: float = 0.6,
        enable_graph: bool = False,
        enable_cache: bool = True,
        enable_synonyms: bool = True,
        enable_stats: bool = True,
        enable_compression: bool = True,
        # v2.14.0: Decay + GroundTruth
        enable_decay: bool = False,
        enable_ground_truth: bool = False,
        decay_config: Optional[Any] = None,
        # v2.15.0: Engram + Spreading
        enable_engram: bool = True,
        enable_spreading: bool = True,
        enable_compression_spectrum: bool = True,
        # v2.18.0: Compression thresholds
        compression_trigger_access: int = 5,
        compression_trigger_apply: int = 3,
        compression_trigger_verify: int = 2,
        engram_ngram_size: int = 3,
        spreading_max_depth: int = 2,
        spreading_decay_factor: float = 0.5,
        spreading_threshold: float = 0.1,
        # v3.0.0-rc.1: CMS Perception Layer
        enable_cms: bool = False,
        cms_token_threshold: int = 8000,
        cms_memory_threshold: int = 1000,
        cms_warning_level: float = 0.8,
        # v3.2.2: Proactive compression
        enable_proactive_compression: bool = True,
        proactive_threshold: float = 0.7,
        max_working_memory: int = 100,
    ):
        # Workspace
        self.workspace = workspace
        self.auto_detect = auto_detect
        # Retrieval
        self.bm25_k1 = bm25_k1
        self.bm25_b = bm25_b
        self.bm25_weight = bm25_weight
        self.keyword_weight = keyword_weight
        self.recency_boost = recency_boost
        self.frequency_boost = frequency_boost
        # Features
        self.enable_gating = enable_gating
        self.gating_threshold = gating_threshold
        self.enable_graph = enable_graph
        self.enable_cache = enable_cache
        self.enable_synonyms = enable_synonyms
        self.enable_stats = enable_stats
        self.enable_compression = enable_compression
        # v2.14.0
        self.enable_decay = enable_decay
        self.enable_ground_truth = enable_ground_truth
        self.decay_config = decay_config
        # v2.15.0
        self.enable_engram = enable_engram
        self.enable_spreading = enable_spreading
        self.enable_compression_spectrum = enable_compression_spectrum
        # v2.18.0
        self.compression_trigger_access = compression_trigger_access
        self.compression_trigger_apply = compression_trigger_apply
        self.compression_trigger_verify = compression_trigger_verify
        self.engram_ngram_size = engram_ngram_size
        self.spreading_max_depth = spreading_max_depth
        self.spreading_decay_factor = spreading_decay_factor
        self.spreading_threshold = spreading_threshold
        # v3.0.0-rc.1
        self.enable_cms = enable_cms
        self.cms_token_threshold = cms_token_threshold
        self.cms_memory_threshold = cms_memory_threshold
        self.cms_warning_level = cms_warning_level
        # v3.2.2
        self.enable_proactive_compression = enable_proactive_compression
        self.proactive_threshold = proactive_threshold
        self.max_working_memory = max_working_memory

    @classmethod
    def default(cls) -> "MemoryConfig":
        """Create default configuration."""
        return cls()

    def to_dict(self) -> dict:
        """Convert to dictionary (for serialization)."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


# ============================================================================
# Usage examples
# ============================================================================

if __name__ == "__main__":
    # Example 1: Auto-detect
    try:
        workspace = ConfigDetector.detect_workspace()
        print(f"Workspace detected: {workspace}")
    except WorkspaceNotFoundError as e:
        print(e)

    print()

    # Example 2: Get workspace info
    try:
        workspace = ConfigDetector.detect_workspace()
        info = ConfigDetector.get_workspace_info(workspace)

        print("Workspace info:")
        print(f"  Path: {info['path']}")
        print(f"  Exists: {info['exists']}")
        print(f"  Valid: {info['is_valid']}")
        print(f"  Markers: {', '.join(info['markers_found'])}")
        print(f"  Memory files: {', '.join(info['memory_files'][:5])}")
    except WorkspaceNotFoundError:
        print("Workspace not found, cannot get info")

    print()

    # Example 3: Suggest workspace
    suggested = ConfigDetector.suggest_workspace()
    if suggested:
        print(f"Suggested workspace: {suggested}")
    else:
        print("Cannot create suggested workspace")
