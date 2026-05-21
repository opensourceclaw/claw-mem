# Copyright 2026 Peter Cheng
"""Tests for config_manager.py - Unified Configuration Management"""

import json
import tempfile
import time
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claw_mem.config_manager import (
    ConfigManager,
    ConfigFileHandler,
    HealthConfig,
    MultimodalConfig,
    PerformanceConfig,
    RetrievalConfig,
    StorageConfig,
    UnifiedConfig,
    get_config,
    reload_config,
)


class TestStorageConfig:
    """Test StorageConfig dataclass"""

    def test_defaults(self):
        """Test default values"""
        config = StorageConfig()
        assert config.workspace == "~/.openclaw/workspace"
        assert config.backup_dir == "~/.claw-mem/backups"
        assert config.max_memory_size_mb == 100
        assert config.auto_save is True
        assert config.auto_save_interval_sec == 300


class TestRetrievalConfig:
    """Test RetrievalConfig dataclass"""

    def test_defaults(self):
        """Test default values"""
        config = RetrievalConfig()
        assert config.max_results == 10
        assert config.cache_size == 1000
        assert config.cache_ttl_seconds == 300
        config.enable_semantic_search is False
        assert config.default_memory_type == "all"


class TestPerformanceConfig:
    """Test PerformanceConfig dataclass"""

    def test_defaults(self):
        """Test default values"""
        config = PerformanceConfig()
        assert config.enable_lazy_loading is True
        assert config.index_chunk_size == 10000
        assert config.max_memory_mb == 500
        assert config.enable_caching is True
        assert config.parallel_operations is True


class TestHealthConfig:
    """Test HealthConfig dataclass"""

    def test_defaults(self):
        """Test default values"""
        config = HealthConfig()
        assert config.enabled is True
        assert config.check_interval_hours == 24
        assert config.auto_cleanup is True
        assert config.max_backup_count == 10
        assert config.alert_on_issues is True


class TestMultimodalConfig:
    """Test MultimodalConfig dataclass"""

    def test_defaults(self):
        """Test default values"""
        config = MultimodalConfig()
        assert config.enabled is False
        assert config.image_storage is False
        assert config.audio_storage is False
        assert config.enable_clip is False
        assert config.clip_model == "auto"


class TestUnifiedConfig:
    """Test UnifiedConfig dataclass"""

    def test_defaults(self):
        """Test default values"""
        config = UnifiedConfig()
        assert config.version == "0.9.0"
        assert isinstance(config.storage, StorageConfig)
        assert isinstance(config.retrieval, RetrievalConfig)
        assert isinstance(config.performance, PerformanceConfig)
        assert isinstance(config.health, HealthConfig)
        assert isinstance(config.multimodal, MultimodalConfig)

    def test_to_dict(self):
        """Test conversion to dictionary"""
        config = UnifiedConfig()
        data = config.to_dict()
        
        assert isinstance(data, dict)
        assert "version" in data
        assert "storage" in data
        assert "retrieval" in data
        assert "performance" in data
        assert "health" in data
        assert "multimodal" in data

    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "version": "0.9.0",
            "storage": {
                "workspace": "/custom/workspace",
                "max_memory_size_mb": 200,
            },
            "retrieval": {
                "max_results": 20,
            },
        }
        
        config = UnifiedConfig.from_dict(data)
        
        assert config.version == "0.9.0"
        assert config.storage.workspace == "/custom/workspace"
        assert config.storage.max_memory_size_mb == 200
        assert config.retrieval.max_results == 20

    def test_from_dict_partial(self):
        """Test creation from partial dictionary"""
        data = {
            "storage": {
                "workspace": "/test/workspace",
            }
        }
        
        config = UnifiedConfig.from_dict(data)
        
        # Should use defaults for missing values
        assert config.storage.workspace == "/test/workspace"
        assert config.retrieval.max_results == 10  # default


class TestConfigFileHandler:
    """Test ConfigFileHandler class"""

    def test_init(self):
        """Test initialization"""
        callback = MagicMock()
        handler = ConfigFileHandler(callback)
        
        assert handler.callback == callback
        assert handler.debounce_timer is None


class TestConfigManager:
    """Test ConfigManager class"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir()
            yield config_dir

    def test_init_default_path(self):
        """Test initialization with default path"""
        with patch("claw_mem.config_manager.Path.home") as mock_home:
            mock_home.return_value = Path("/test/home")
            
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch.object(ConfigManager, "CONFIG_PATH", Path(tmpdir) / "config.yml"):
                    with patch.object(ConfigManager, "OLD_CONFIG_PATH", Path(tmpdir) / "config.json"):
                        manager = ConfigManager(enable_hot_reload=False)
                        assert manager.config_path.name == "config.yml"

    def test_init_custom_path(self, temp_config_dir):
        """Test initialization with custom path"""
        config_path = temp_config_dir / "custom.yml"
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        
        assert manager.config_path == config_path

    def test_load_nonexistent(self, temp_config_dir):
        """Test loading non-existent config creates default"""
        config_path = temp_config_dir / "new.yml"
        
        # Config shouldn't exist initially
        assert not config_path.exists()
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        
        # After init, config should be created
        # (load creates default if file doesn't exist)

    def test_load_existing(self, temp_config_dir):
        """Test loading existing config"""
        config_path = temp_config_dir / "existing.yml"
        
        # Create a config file
        config_data = {
            "version": "0.9.0",
            "storage": {
                "workspace": "/test/workspace",
                "max_memory_size_mb": 150,
            },
        }
        
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        
        assert manager.config.storage.workspace == "/test/workspace"
        assert manager.config.storage.max_memory_size_mb == 150

    def test_load_use_cache(self, temp_config_dir):
        """Test config loading with cache"""
        config_path = temp_config_dir / "cache.yml"
        
        config_data = {"version": "0.9.0"}
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        
        # Load with cache - should use cached value
        result = manager.load(use_cache=True)
        assert result is True

    def test_save(self, temp_config_dir):
        """Test saving config"""
        config_path = temp_config_dir / "save.yml"
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        manager.config.storage.workspace = "/saved/workspace"
        
        manager.save()
        
        assert config_path.exists()
        
        # Verify saved content
        with open(config_path) as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data["storage"]["workspace"] == "/saved/workspace"

    def test_get(self, temp_config_dir):
        """Test getting config value"""
        config_path = temp_config_dir / "get.yml"
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        
        # Get existing value
        workspace = manager.get("storage.workspace")
        assert workspace == "~/.openclaw/workspace"
        
        # Get with default
        value = manager.get("nonexistent.key", "default_value")
        assert value == "default_value"

    def test_set(self, temp_config_dir):
        """Test setting config value"""
        config_path = temp_config_dir / "set.yml"
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        
        # Set value without saving
        manager.set("storage.workspace", "/new/workspace", save=False)
        assert manager.config.storage.workspace == "/new/workspace"

    def test_set_invalid_key(self, temp_config_dir):
        """Test setting invalid key raises error"""
        config_path = temp_config_dir / "invalid.yml"
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        
        with pytest.raises(KeyError):
            manager.set("invalid.key", "value")

    def test_validate_valid(self, temp_config_dir):
        """Test validation with valid config"""
        config_path = temp_config_dir / "valid.yml"
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        
        errors = manager.validate()
        assert errors == []

    def test_validate_invalid_storage(self, temp_config_dir):
        """Test validation with invalid storage config"""
        config_path = temp_config_dir / "invalid_storage.yml"
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        manager.config.storage.max_memory_size_mb = 5  # Less than minimum
        
        errors = manager.validate()
        
        assert any("max_memory_size_mb" in err for err in errors)

    def test_validate_invalid_retrieval(self, temp_config_dir):
        """Test validation with invalid retrieval config"""
        config_path = temp_config_dir / "invalid_retrieval.yml"
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        manager.config.retrieval.max_results = 0  # Less than minimum
        
        errors = manager.validate()
        
        assert any("max_results" in err for err in errors)

    def test_validate_invalid_performance(self, temp_config_dir):
        """Test validation with invalid performance config"""
        config_path = temp_config_dir / "invalid_performance.yml"
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        manager.config.performance.max_memory_mb = 50  # Less than minimum
        
        errors = manager.validate()
        
        assert any("max_memory_mb" in err for err in errors)

    def test_validate_invalid_health(self, temp_config_dir):
        """Test validation with invalid health config"""
        config_path = temp_config_dir / "invalid_health.yml"
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        manager.config.health.check_interval_hours = 0  # Less than minimum
        
        errors = manager.validate()
        
        assert any("check_interval_hours" in err for err in errors)

    def test_register_observer(self, temp_config_dir):
        """Test registering observer"""
        config_path = temp_config_dir / "observer.yml"
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        
        callback = MagicMock()
        manager.register_observer(callback)
        
        assert callback in manager._observers

    def test_unregister_observer(self, temp_config_dir):
        """Test unregistering observer"""
        config_path = temp_config_dir / "unregister.yml"
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        
        callback = MagicMock()
        manager.register_observer(callback)
        manager.unregister_observer(callback)
        
        assert callback not in manager._observers

    def test_reset_to_defaults(self, temp_config_dir):
        """Test resetting to defaults"""
        config_path = temp_config_dir / "reset.yml"
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        manager.config.storage.workspace = "/custom/path"
        
        manager.reset_to_defaults()
        
        assert manager.config.storage.workspace == "~/.openclaw/workspace"

    def test_get_stats(self, temp_config_dir):
        """Test getting config stats"""
        config_path = temp_config_dir / "stats.yml"
        
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)
        
        stats = manager.get_stats()
        
        assert "config_path" in stats
        assert "config_exists" in stats
        assert "version" in stats
        assert "hot_reload_enabled" in stats


class TestGlobalConfig:
    """Test global config functions"""

    def test_get_config(self):
        """Test getting global config instance"""
        # Reset global config
        import claw_mem.config_manager as cm
        cm._global_config = None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yml"
            
            with patch.object(ConfigManager, "CONFIG_PATH", config_path):
                config = get_config()
                
                assert isinstance(config, ConfigManager)

    def test_reload_config(self):
        """Test reloading global config"""
        import claw_mem.config_manager as cm
        
        # Set up a mock config
        mock_config = MagicMock()
        cm._global_config = mock_config
        
        reload_config()
        
        mock_config.load.assert_called_once()
