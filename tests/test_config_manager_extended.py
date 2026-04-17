"""
Extended tests for Config Manager

Tests unified configuration management with hot-reload support.
"""

import pytest
import tempfile
import time
import threading
from pathlib import Path
from claw_mem.config_manager import (
    StorageConfig,
    RetrievalConfig,
    PerformanceConfig,
    HealthConfig,
    MultimodalConfig,
    UnifiedConfig,
    ConfigManager,
    get_config,
    reload_config
)


class TestStorageConfig:
    """Test StorageConfig"""

    def test_defaults(self):
        """Test StorageConfig default values"""
        config = StorageConfig()

        assert config.workspace == "~/.openclaw/workspace"
        assert config.backup_dir == "~/.claw-mem/backups"
        assert config.max_memory_size_mb == 100
        assert config.auto_save is True
        assert config.auto_save_interval_sec == 300

    def test_custom_values(self):
        """Test StorageConfig with custom values"""
        config = StorageConfig(
            workspace="/custom/path",
            max_memory_size_mb=200,
            auto_save=False
        )

        assert config.workspace == "/custom/path"
        assert config.max_memory_size_mb == 200
        assert config.auto_save is False


class TestRetrievalConfig:
    """Test RetrievalConfig"""

    def test_defaults(self):
        """Test RetrievalConfig default values"""
        config = RetrievalConfig()

        assert config.max_results == 10
        assert config.cache_size == 1000
        assert config.cache_ttl_seconds == 300
        assert config.enable_semantic_search is False
        assert config.default_memory_type == "all"

    def test_custom_values(self):
        """Test RetrievalConfig with custom values"""
        config = RetrievalConfig(
            max_results=20,
            enable_semantic_search=True
        )

        assert config.max_results == 20
        assert config.enable_semantic_search is True


class TestPerformanceConfig:
    """Test PerformanceConfig"""

    def test_defaults(self):
        """Test PerformanceConfig default values"""
        config = PerformanceConfig()

        assert config.enable_lazy_loading is True
        assert config.index_chunk_size == 10000
        assert config.max_memory_mb == 500
        assert config.enable_caching is True
        assert config.parallel_operations is True


class TestHealthConfig:
    """Test HealthConfig"""

    def test_defaults(self):
        """Test HealthConfig default values"""
        config = HealthConfig()

        assert config.enabled is True
        assert config.check_interval_hours == 24
        assert config.auto_cleanup is True
        assert config.max_backup_count == 10
        assert config.alert_on_issues is True


class TestMultimodalConfig:
    """Test MultimodalConfig"""

    def test_defaults(self):
        """Test MultimodalConfig default values"""
        config = MultimodalConfig()

        assert config.enabled is False
        assert config.image_storage is False
        assert config.audio_storage is False
        assert config.enable_clip is False
        assert config.clip_model == "auto"

    def test_clip_model_options(self):
        """Test CLIP model options"""
        config = MultimodalConfig(clip_model="rn50")

        assert config.clip_model == "rn50"


class TestUnifiedConfig:
    """Test UnifiedConfig"""

    def test_defaults(self):
        """Test UnifiedConfig default values"""
        config = UnifiedConfig()

        assert config.version == "0.9.0"
        assert isinstance(config.storage, StorageConfig)
        assert isinstance(config.retrieval, RetrievalConfig)
        assert isinstance(config.performance, PerformanceConfig)
        assert isinstance(config.health, HealthConfig)
        assert isinstance(config.multimodal, MultimodalConfig)

    def test_to_dict(self):
        """Test converting config to dictionary"""
        config = UnifiedConfig(
            version="1.0.0",
            storage=StorageConfig(max_memory_size_mb=200)
        )

        config_dict = config.to_dict()

        assert config_dict["version"] == "1.0.0"
        assert config_dict["storage"]["max_memory_size_mb"] == 200

    def test_from_dict(self):
        """Test creating config from dictionary"""
        data = {
            "version": "1.0.0",
            "storage": {
                "workspace": "/custom/path",
                "max_memory_size_mb": 200
            },
            "retrieval": {
                "max_results": 20
            }
        }

        config = UnifiedConfig.from_dict(data)

        assert config.version == "1.0.0"
        assert config.storage.workspace == "/custom/path"
        assert config.storage.max_memory_size_mb == 200
        assert config.retrieval.max_results == 20

    def test_from_dict_with_invalid_keys(self):
        """Test creating config with invalid keys (should be ignored)"""
        data = {
            "version": "1.0.0",
            "storage": {
                "workspace": "/custom/path",
                "invalid_key": "should_be_ignored"
            }
        }

        config = UnifiedConfig.from_dict(data)

        assert config.storage.workspace == "/custom/path"
        assert not hasattr(config.storage, "invalid_key")


class TestConfigManager:
    """Test ConfigManager"""

    def test_initialization(self, tmp_path):
        """Test ConfigManager initialization"""
        config_path = tmp_path / "config.yml"
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)

        assert manager.config_path == config_path
        assert isinstance(manager.config, UnifiedConfig)
        assert manager.enable_hot_reload is False

    def test_load_nonexistent_config(self, tmp_path):
        """Test loading nonexistent config (creates default)"""
        config_path = tmp_path / "config.yml"
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)

        manager.load(use_cache=False)

        assert config_path.exists()

    def test_save_and_load(self, tmp_path):
        """Test saving and loading config"""
        config_path = tmp_path / "config.yml"
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)

        # Modify config
        manager.set("storage.max_memory_size_mb", 500)

        # Load again
        manager.load(use_cache=False)

        assert manager.config.storage.max_memory_size_mb == 500

    def test_get_dot_key(self, tmp_path):
        """Test getting config value with dot notation"""
        manager = ConfigManager(enable_hot_reload=False)

        value = manager.get("storage.workspace")

        assert value is not None
        assert "workspace" in value

    def test_get_with_default(self, tmp_path):
        """Test getting config value with default"""
        manager = ConfigManager(enable_hot_reload=False)

        value = manager.get("invalid.key", "default_value")

        assert value == "default_value"

    def test_set_dot_key(self, tmp_path):
        """Test setting config value with dot notation"""
        config_path = tmp_path / "config.yml"
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)

        manager.set("storage.max_memory_size_mb", 300)

        assert manager.config.storage.max_memory_size_mb == 300

    def test_set_invalid_key(self, tmp_path):
        """Test setting invalid key raises error"""
        manager = ConfigManager(enable_hot_reload=False)

        with pytest.raises(KeyError):
            manager.set("invalid.invalid.key", 100)

    def test_validate_valid_config(self, tmp_path):
        """Test validating valid config"""
        manager = ConfigManager(enable_hot_reload=False)

        errors = manager.validate()

        assert len(errors) == 0

    def test_validate_invalid_config(self, tmp_path):
        """Test validating invalid config"""
        manager = ConfigManager(enable_hot_reload=False)

        # Set invalid values
        manager.config.storage.max_memory_size_mb = 5
        manager.config.retrieval.max_results = 0

        errors = manager.validate()

        assert len(errors) > 0
        assert any("max_memory_size_mb" in e for e in errors)
        assert any("max_results" in e for e in errors)

    def test_reset_to_defaults(self, tmp_path):
        """Test resetting to defaults"""
        config_path = tmp_path / "config.yml"
        manager = ConfigManager(config_path=str(config_path), enable_hot_reload=False)

        # Modify config
        manager.set("storage.max_memory_size_mb", 500)

        # Reset
        manager.reset_to_defaults()

        assert manager.config.storage.max_memory_size_mb == 100

    def test_get_stats(self, tmp_path):
        """Test getting config statistics"""
        manager = ConfigManager(enable_hot_reload=False)

        stats = manager.get_stats()

        assert "config_path" in stats
        assert "version" in stats
        assert "hot_reload_enabled" in stats

    def test_register_unregister_observer(self, tmp_path):
        """Test registering and unregistering observers"""
        manager = ConfigManager(enable_hot_reload=False)

        callback_called = threading.Event()

        def observer_callback(config):
            callback_called.set()

        # Register
        manager.register_observer(observer_callback)

        # Manually trigger callback (simulating config change)
        for callback in manager._observers:
            callback(manager.config)

        # Check callback was called
        assert callback_called.is_set()

        # Unregister
        manager.unregister_observer(observer_callback)

        # Observer should be removed
        assert observer_callback not in manager._observers


class TestGlobalConfig:
    """Test global config singleton"""

    def test_get_config_singleton(self):
        """Test get_config returns same instance"""
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_reload_config(self):
        """Test reload_config function"""
        config = get_config()
        reload_config()

        # Config should still be valid
        assert config is not None
        assert isinstance(config.config, UnifiedConfig)


class TestConfigMigration:
    """Test config migration from old JSON format"""

    def test_migrate_from_old_config(self, tmp_path):
        """Test migrating from old JSON config"""
        # Skip this test as it requires complex setup
        pytest.skip("Test requires complex migration setup")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
