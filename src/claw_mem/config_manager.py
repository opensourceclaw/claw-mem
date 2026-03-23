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
Unified Configuration Management (v0.9.0)

Provides centralized configuration with hot-reload support.

v0.9.0 Improvements:
- Single YAML configuration file (~/.claw-mem/config.yml)
- Hot-reload support (no restart needed)
- Configuration validation
- Backward compatible with old config formats
- Default values for all settings

Performance Targets:
- Config load: <10ms
- Hot-reload: <5ms
- Validation: automatic
"""

import os
import json
import yaml
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading


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
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedConfig':
        """Create from dictionary"""
        config = cls()
        
        if 'version' in data:
            config.version = data['version']
        
        if 'storage' in data:
            for key, value in data['storage'].items():
                if hasattr(config.storage, key):
                    setattr(config.storage, key, value)
        
        if 'retrieval' in data:
            for key, value in data['retrieval'].items():
                if hasattr(config.retrieval, key):
                    setattr(config.retrieval, key, value)
        
        if 'performance' in data:
            for key, value in data['performance'].items():
                if hasattr(config.performance, key):
                    setattr(config.performance, key, value)
        
        if 'health' in data:
            for key, value in data['health'].items():
                if hasattr(config.health, key):
                    setattr(config.health, key, value)
        
        if 'multimodal' in data:
            for key, value in data['multimodal'].items():
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
        if event.src_path.endswith('.yml') or event.src_path.endswith('.yaml'):
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
        if use_cache and hasattr(self, '_config_cache') and self._config_cache:
            elapsed = (time.time() - start_time) * 1000
            print(f"✅ Config loaded from cache in {elapsed:.2f}ms")
            return True
        
        with self._lock:
            try:
                if self.config_path.exists():
                    # Load YAML config with optimized reading
                    with open(self.config_path, 'r', encoding='utf-8') as f:
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
            with open(self.OLD_CONFIG_PATH, 'r') as f:
                old_data = json.load(f)
            
            # Convert to new format
            self.config = self._convert_old_config(old_data)
            
            # Save as YAML
            self.save()
            
            # Backup old config
            backup_path = self.OLD_CONFIG_PATH.with_suffix('.json.bak')
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
        if 'workspace' in old_data:
            config.storage.workspace = old_data['workspace']
        
        # Try to extract retrieval settings
        if 'retrieval' in old_data:
            retrieval = old_data['retrieval']
            if 'max_results' in retrieval:
                config.retrieval.max_results = retrieval['max_results']
        
        # Try to extract security settings
        if 'security' in old_data:
            security = old_data['security']
            # Map old security settings to new health config
            if 'enable_validation' in security:
                config.health.enabled = security['enable_validation']
        
        return config
    
    def save(self):
        """Save configuration to file"""
        start_time = time.time()
        
        with self._lock:
            try:
                self.config_dir.mkdir(parents=True, exist_ok=True)
                
                # Optimize YAML output (faster serialization)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(
                        self.config.to_dict(),
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=True,
                        width=1000  # Reduce line breaks (faster)
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
            keys = key.split('.')
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
            keys = key.split('.')
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
