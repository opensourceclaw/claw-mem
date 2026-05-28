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

import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

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
        enable_compression_spectrum: bool = True,
        # v2.18.0: Compression thresholds
        compression_trigger_access: int = 5,
        compression_trigger_apply: int = 3,
        compression_trigger_verify: int = 2,
        # v4.7.0: Semantic merge + tiered decay + conflict detection
        enable_merge: bool = True,
        merge_interval: int = 100,
        merge_sim_threshold: float = 0.65,
        enable_tiered_decay: bool = False,
        tiered_hot_ttl: int = 3600,
        tiered_warm_ttl_days: int = 7,
        tiered_cold_ttl_days: int = 30,
        enable_conflict_detect: bool = True,
        llm_provider: str = "auto",
        llm_model: str = "gpt-4o-mini",
        # v4.8.0: Query reconstruction + hybrid routing
        enable_query_reconstruction: bool = True,
        enable_hybrid_routing: bool = False,
        # v4.9.0: Context control plane
        enable_context_control: bool = False,
        enable_memory_injector: bool = True,
        injector_max_tokens: int = 2000,
        injector_diversity_threshold: float = 0.8,
        injector_relevance_threshold: float = 0.3,
        injector_recency_weight: float = 0.4,
        enable_confidence_gate: bool = True,
        confidence_high_threshold: float = 0.7,
        confidence_low_threshold: float = 0.4,
        # v4.10.0: OpenIE extraction + graph reasoning
        enable_openie: bool = False,
        enable_graph_reasoner: bool = False,
        openie_mode: str = "auto",  # "llm" | "rule" | "auto"
        openie_llm_max_tokens: int = 512,
        graph_reasoner_max_depth: int = 3,
        # v4.11.0: Skill extraction from triplets
        enable_skill_extraction: bool = True,
        skill_extraction_mode: str = "auto",  # "llm" | "rule" | "auto"
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
        self.enable_compression_spectrum = enable_compression_spectrum
        # v2.18.0
        self.compression_trigger_access = compression_trigger_access
        self.compression_trigger_apply = compression_trigger_apply
        self.compression_trigger_verify = compression_trigger_verify
        # v4.7.0
        self.enable_merge = enable_merge
        self.merge_interval = merge_interval
        self.merge_sim_threshold = merge_sim_threshold
        self.enable_tiered_decay = enable_tiered_decay
        self.tiered_hot_ttl = tiered_hot_ttl
        self.tiered_warm_ttl_days = tiered_warm_ttl_days
        self.tiered_cold_ttl_days = tiered_cold_ttl_days
        self.enable_conflict_detect = enable_conflict_detect
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        # v4.8.0
        self.enable_query_reconstruction = enable_query_reconstruction
        self.enable_hybrid_routing = enable_hybrid_routing
        # v4.9.0
        self.enable_context_control = enable_context_control
        self.enable_memory_injector = enable_memory_injector
        self.injector_max_tokens = injector_max_tokens
        self.injector_diversity_threshold = injector_diversity_threshold
        self.injector_relevance_threshold = injector_relevance_threshold
        self.injector_recency_weight = injector_recency_weight
        self.enable_confidence_gate = enable_confidence_gate
        self.confidence_high_threshold = confidence_high_threshold
        self.confidence_low_threshold = confidence_low_threshold
        # v4.10.0
        self.enable_openie = enable_openie
        self.enable_graph_reasoner = enable_graph_reasoner
        self.openie_mode = openie_mode
        self.openie_llm_max_tokens = openie_llm_max_tokens
        self.graph_reasoner_max_depth = graph_reasoner_max_depth
        # v4.11.0
        self.enable_skill_extraction = enable_skill_extraction
        self.skill_extraction_mode = skill_extraction_mode

    @classmethod
    def default(cls) -> "MemoryConfig":
        """Create default configuration."""
        return cls()

    def to_dict(self) -> dict:
        """Convert to dictionary (for serialization)."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


##############################################################################
# Unified Configuration Management (v0.9.0)
##############################################################################


@dataclass
class StorageConfig:
    """Storage configuration"""

    workspace: str = "~/.openclaw/workspace"
    backup_dir: str = "~/.claw-mem/backups"
    max_memory_size_mb: int = 100
    auto_save: bool = True
    auto_save_interval_sec: int = 300


@dataclass
class RetrievalConfig:
    """Retrieval configuration"""

    max_results: int = 10
    cache_size: int = 1000
    cache_ttl_seconds: int = 300
    enable_semantic_search: bool = False
    default_memory_type: str = "all"  # all, episodic, semantic, procedural


@dataclass
class PerformanceConfig:
    """Performance configuration"""

    enable_lazy_loading: bool = True
    index_chunk_size: int = 10000
    max_memory_mb: int = 500
    enable_caching: bool = True
    parallel_operations: bool = True


@dataclass
class HealthConfig:
    """Health check configuration"""

    enabled: bool = True
    check_interval_hours: int = 24
    auto_cleanup: bool = True
    max_backup_count: int = 10
    alert_on_issues: bool = True


@dataclass
class MultimodalConfig:
    """Multimodal configuration (future use)"""

    enabled: bool = False
    image_storage: bool = False
    audio_storage: bool = False
    enable_clip: bool = False  # Disabled by default for old devices
    clip_model: str = "auto"  # auto, rn50, vit-b-32


@dataclass
class UnifiedConfig:
    """
    Unified Configuration

    All configuration settings in one place
    """

    version: str = "0.9.0"
    storage: StorageConfig = field(default_factory=StorageConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    health: HealthConfig = field(default_factory=HealthConfig)
    multimodal: MultimodalConfig = field(default_factory=MultimodalConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedConfig":
        """Create from dictionary"""
        config = cls()

        if "version" in data:
            config.version = data["version"]

        if "storage" in data:
            for key, value in data["storage"].items():
                if hasattr(config.storage, key):
                    setattr(config.storage, key, value)

        if "retrieval" in data:
            for key, value in data["retrieval"].items():
                if hasattr(config.retrieval, key):
                    setattr(config.retrieval, key, value)

        if "performance" in data:
            for key, value in data["performance"].items():
                if hasattr(config.performance, key):
                    setattr(config.performance, key, value)

        if "health" in data:
            for key, value in data["health"].items():
                if hasattr(config.health, key):
                    setattr(config.health, key, value)

        if "multimodal" in data:
            for key, value in data["multimodal"].items():
                if hasattr(config.multimodal, key):
                    setattr(config.multimodal, key, value)

        return config


class ConfigFileHandler(FileSystemEventHandler):
    """Handle config file changes for hot-reload"""

    def __init__(self, callback):
        self.callback = callback
        self.debounce_timer = None

    def on_modified(self, event):
        """Handle file modification"""
        if event.src_path.endswith(".yml") or event.src_path.endswith(".yaml"):
            # Debounce - wait 500ms after last change
            if self.debounce_timer:
                self.debounce_timer.cancel()

            self.debounce_timer = threading.Timer(0.5, self.callback)
            self.debounce_timer.start()


class ConfigManager:
    """
    Unified Configuration Manager

    Features:
    - Single YAML config file
    - Hot-reload support
    - Validation
    - Backward compatibility
    - Thread-safe
    """

    CONFIG_PATH = Path.home() / ".claw-mem" / "config.yml"
    OLD_CONFIG_PATH = Path.home() / ".claw-mem" / "config.json"

    def __init__(self, config_path: Optional[str] = None, enable_hot_reload: bool = True):
        """
        Initialize configuration manager

        Args:
            config_path: Custom config path (optional)
            enable_hot_reload: Enable hot-reload on config changes (default: True)
        """
        self.config_path = Path(config_path).expanduser() if config_path else self.CONFIG_PATH
        self.config = UnifiedConfig()
        self.config_dir = self.config_path.parent
        self.enable_hot_reload = enable_hot_reload
        self._lock = threading.RLock()
        self._observers = []

        # Create config directory
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load or create config
        self.load()

        # Setup hot-reload
        if self.enable_hot_reload:
            self._setup_hot_reload()

        # Initialize config cache (optimization)
        self._config_cache = False

    def _setup_hot_reload(self):
        """Setup file watcher for hot-reload"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        observer = Observer()
        handler = ConfigFileHandler(self._on_config_change)
        observer.schedule(handler, str(self.config_dir), recursive=False)
        observer.start()

    def _on_config_change(self):
        """Handle config file change"""
        print("📝 Config file changed, reloading...")
        try:
            self.load()
            print("✅ Config reloaded successfully")

            # Notify observers
            for callback in self._observers:
                callback(self.config)

        except Exception as e:
            print(f"❌ Failed to reload config: {e}")

    def load(self, use_cache: bool = True) -> bool:
        """
        Load configuration from file

        Args:
            use_cache: Use cached config if available (default: True)

        Returns:
            True if successful
        """
        start_time = time.time()

        # Check cache first (optimization)
        if use_cache and hasattr(self, "_config_cache") and self._config_cache:
            elapsed = (time.time() - start_time) * 1000
            print(f"✅ Config loaded from cache in {elapsed:.2f}ms")
            return True

        with self._lock:
            try:
                if self.config_path.exists():
                    # Load YAML config with optimized reading
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        # Read all at once (faster than line by line)
                        content = f.read()
                        data = yaml.safe_load(content)

                    if data:
                        self.config = UnifiedConfig.from_dict(data)
                        # Cache the config (optimization)
                        self._config_cache = True

                    elapsed = (time.time() - start_time) * 1000
                    print(f"✅ Config loaded in {elapsed:.2f}ms")
                    return True

                elif self.OLD_CONFIG_PATH.exists():
                    # Migrate from old JSON config
                    print("📦 Migrating from old config.json...")
                    self._migrate_old_config()
                    return True

                else:
                    # Create default config
                    print("📝 Creating default config...")
                    self.save()
                    self._config_cache = True
                    return True

            except Exception as e:
                print(f"⚠️  Failed to load config: {e}")
                print("   Using default configuration")
                return False

    def _migrate_old_config(self):
        """Migrate from old JSON config to YAML"""
        try:
            with open(self.OLD_CONFIG_PATH, "r") as f:
                old_data = json.load(f)

            # Convert to new format
            self.config = self._convert_old_config(old_data)

            # Save as YAML
            self.save()

            # Backup old config
            backup_path = self.OLD_CONFIG_PATH.with_suffix(".json.bak")
            self.OLD_CONFIG_PATH.rename(backup_path)

            print(f"✅ Migration complete. Old config backed up to {backup_path}")

        except Exception as e:
            print(f"⚠️  Migration failed: {e}")
            print("   Creating new default config")
            self.save()

    def _convert_old_config(self, old_data: Dict) -> UnifiedConfig:
        """Convert old config format to new format"""
        config = UnifiedConfig()

        # Try to extract workspace from old config
        if "workspace" in old_data:
            config.storage.workspace = old_data["workspace"]

        # Try to extract retrieval settings
        if "retrieval" in old_data:
            retrieval = old_data["retrieval"]
            if "max_results" in retrieval:
                config.retrieval.max_results = retrieval["max_results"]

        # Try to extract security settings
        if "security" in old_data:
            security = old_data["security"]
            # Map old security settings to new health config
            if "enable_validation" in security:
                config.health.enabled = security["enable_validation"]

        return config

    def save(self):
        """Save configuration to file"""
        start_time = time.time()

        with self._lock:
            try:
                self.config_dir.mkdir(parents=True, exist_ok=True)

                # Optimize YAML output (faster serialization)
                with open(self.config_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        self.config.to_dict(),
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=True,
                        width=1000,  # Reduce line breaks (faster)
                    )

                # Invalidate cache (will reload next time)
                self._config_cache = False

                elapsed = (time.time() - start_time) * 1000
                print(f"✅ Config saved in {elapsed:.2f}ms")

            except Exception as e:
                print(f"❌ Failed to save config: {e}")
                raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            key: Dot-separated key (e.g., "storage.workspace")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        with self._lock:
            keys = key.split(".")
            value = self.config

            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return default

            return value

    def set(self, key: str, value: Any, save: bool = True):
        """
        Set configuration value

        Args:
            key: Dot-separated key (e.g., "storage.workspace")
            value: Value to set
            save: Save to file immediately (default: True)
        """
        with self._lock:
            keys = key.split(".")
            obj = self.config

            # Navigate to parent
            for k in keys[:-1]:
                if hasattr(obj, k):
                    obj = getattr(obj, k)
                else:
                    raise KeyError(f"Invalid config key: {key}")

            # Set value
            if hasattr(obj, keys[-1]):
                setattr(obj, keys[-1], value)

                if save:
                    self.save()
            else:
                raise KeyError(f"Invalid config key: {key}")

    def validate(self) -> List[str]:
        """
        Validate configuration

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate storage
        if self.config.storage.max_memory_size_mb < 10:
            errors.append("storage.max_memory_size_mb must be >= 10")

        # Validate retrieval
        if self.config.retrieval.max_results < 1:
            errors.append("retrieval.max_results must be >= 1")

        if self.config.retrieval.cache_size < 100:
            errors.append("retrieval.cache_size must be >= 100")

        # Validate performance
        if self.config.performance.max_memory_mb < 100:
            errors.append("performance.max_memory_mb must be >= 100")

        # Validate health
        if self.config.health.check_interval_hours < 1:
            errors.append("health.check_interval_hours must be >= 1")

        return errors

    def register_observer(self, callback):
        """Register callback for config changes"""
        self._observers.append(callback)

    def unregister_observer(self, callback):
        """Unregister callback"""
        if callback in self._observers:
            self._observers.remove(callback)

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        with self._lock:
            self.config = UnifiedConfig()
            self.save()
            print("✅ Config reset to defaults")

    def get_stats(self) -> Dict[str, Any]:
        """Get configuration statistics"""
        return {
            "config_path": str(self.config_path),
            "config_exists": self.config_path.exists(),
            "version": self.config.version,
            "hot_reload_enabled": self.enable_hot_reload,
            "observers": len(self._observers),
        }


# Global config instance (singleton)
_global_config: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global config instance"""
    global _global_config

    if _global_config is None:
        _global_config = ConfigManager()

    return _global_config


def reload_config():
    """Reload global config"""
    global _global_config

    if _global_config:
        _global_config.load()
    else:
        _global_config = ConfigManager()


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
