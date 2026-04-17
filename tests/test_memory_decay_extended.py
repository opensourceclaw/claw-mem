"""
Extended tests for Memory Decay

Tests memory decay mechanism for automatic archival.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from claw_mem.memory_decay import MemoryDecay


class TestMemoryDecay:
    """Test MemoryDecay"""

    def test_initialization(self, tmp_path):
        """Test MemoryDecay initialization"""
        decay = MemoryDecay(workspace=str(tmp_path))

        assert decay.workspace == tmp_path.resolve()
        assert decay.decay_constants['episodic'] == 7
        assert decay.decay_constants['semantic'] == 90
        assert decay.decay_constants['procedural'] == 180

    def test_initialization_custom_constants(self, tmp_path):
        """Test initialization with custom constants"""
        custom_constants = {
            'episodic': 5,
            'semantic': 60,
            'procedural': 120
        }

        decay = MemoryDecay(workspace=str(tmp_path), custom_constants=custom_constants)

        assert decay.decay_constants['episodic'] == 5
        assert decay.decay_constants['semantic'] == 60
        assert decay.decay_constants['procedural'] == 120

    def test_calculate_activation_episodic(self, tmp_path):
        """Test calculating activation for episodic memory"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'memory_type': 'episodic',
            'accessed_at': datetime.now() - timedelta(days=3),
            'activation_level': 1.0
        }

        activation = decay.calculate_activation(memory)

        # 3 days with 7-day half-life: exp(-3/7) ≈ 0.65
        assert 0.6 < activation < 0.7

    def test_calculate_activation_semantic(self, tmp_path):
        """Test calculating activation for semantic memory"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'memory_type': 'semantic',
            'accessed_at': datetime.now() - timedelta(days=10),
            'activation_level': 1.0
        }

        activation = decay.calculate_activation(memory)

        # 10 days with 90-day half-life: exp(-10/90) ≈ 0.89
        assert 0.88 < activation < 0.9

    def test_calculate_activation_with_string_timestamp(self, tmp_path):
        """Test calculating activation with string timestamp"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'memory_type': 'episodic',
            'accessed_at': (datetime.now() - timedelta(days=5)).isoformat(),
            'activation_level': 1.0
        }

        activation = decay.calculate_activation(memory)

        assert 0.4 < activation < 0.6

    def test_calculate_activation_no_accessed_at(self, tmp_path):
        """Test calculating activation without accessed_at"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'memory_type': 'episodic',
            'activation_level': 0.5
        }

        activation = decay.calculate_activation(memory)

        # Should return current activation
        assert activation == 0.5

    def test_calculate_activation_clamp_to_zero(self, tmp_path):
        """Test activation approaches but doesn't reach zero"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'memory_type': 'episodic',
            'accessed_at': datetime.now() - timedelta(days=365),  # Very old
            'activation_level': 0.1
        }

        activation = decay.calculate_activation(memory)

        # Should be very close to zero (but not exactly zero due to exp())
        assert activation < 0.01
        assert activation >= 0.0

    def test_calculate_activation_clamp_to_one(self, tmp_path):
        """Test activation is clamped to maximum 1.0"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'memory_type': 'episodic',
            'accessed_at': datetime.now(),  # Just accessed
            'activation_level': 1.0
        }

        activation = decay.calculate_activation(memory)

        # Should be clamped to 1.0
        assert activation == 1.0

    def test_calculate_activation_default_memory_type(self, tmp_path):
        """Test calculating activation with default memory type"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'accessed_at': datetime.now() - timedelta(days=5),
            'activation_level': 1.0
        }

        activation = decay.calculate_activation(memory)

        # Should use episodic default (7-day half-life)
        assert 0.4 < activation < 0.6

    def test_should_archive_low_activation(self, tmp_path):
        """Test should_archive for low activation memory"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'memory_type': 'episodic',
            'accessed_at': datetime.now() - timedelta(days=30),
            'activation_level': 0.1
        }

        should_archive = decay.should_archive(memory)

        # Low activation should be archived
        assert should_archive is True

    def test_should_archive_high_activation(self, tmp_path):
        """Test should_archive for high activation memory"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'memory_type': 'episodic',
            'accessed_at': datetime.now(),
            'activation_level': 1.0
        }

        should_archive = decay.should_archive(memory)

        # High activation should not be archived
        assert should_archive is False

    def test_should_expire_episodic_old(self, tmp_path):
        """Test should_expire for old episodic memory"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'memory_type': 'episodic',
            'accessed_at': datetime.now() - timedelta(days=35),  # > 30 days
            'activation_level': 0.1
        }

        should_expire = decay.should_expire(memory)

        # Old episodic memory should expire
        assert should_expire is True

    def test_should_expire_episodic_recent(self, tmp_path):
        """Test should_expire for recent episodic memory"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'memory_type': 'episodic',
            'accessed_at': datetime.now() - timedelta(days=10),
            'activation_level': 0.5
        }

        should_expire = decay.should_expire(memory)

        # Recent episodic memory should not expire
        assert should_expire is False

    def test_should_expire_semantic(self, tmp_path):
        """Test semantic memories never expire"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'memory_type': 'semantic',
            'accessed_at': datetime.now() - timedelta(days=365),
            'activation_level': 0.1
        }

        should_expire = decay.should_expire(memory)

        # Semantic memories never expire
        assert should_expire is False

    def test_should_expire_procedural(self, tmp_path):
        """Test procedural memories never expire"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'memory_type': 'procedural',
            'accessed_at': datetime.now() - timedelta(days=365),
            'activation_level': 0.1
        }

        should_expire = decay.should_expire(memory)

        # Procedural memories never expire
        assert should_expire is False

    def test_should_expire_no_accessed_at(self, tmp_path):
        """Test should_expire without accessed_at"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'memory_type': 'episodic',
            'activation_level': 0.5
        }

        should_expire = decay.should_expire(memory)

        # Without accessed_at, cannot expire
        assert should_expire is False

    def test_process_memories_mixed(self, tmp_path):
        """Test processing mixed memories"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memories = [
            {
                'id': 'mem_001',
                'memory_type': 'episodic',
                'accessed_at': datetime.now() - timedelta(days=35),
                'activation_level': 0.1
            },
            {
                'id': 'mem_002',
                'memory_type': 'episodic',
                'accessed_at': datetime.now() - timedelta(days=30),
                'activation_level': 0.2
            },
            {
                'id': 'mem_003',
                'memory_type': 'semantic',
                'accessed_at': datetime.now() - timedelta(days=10),
                'activation_level': 0.8
            }
        ]

        result = decay.process_memories(memories)

        assert len(result['active']) >= 1
        assert len(result['archive']) >= 1
        assert len(result['expire']) == 1

    def test_process_memories_empty(self, tmp_path):
        """Test processing empty memory list"""
        decay = MemoryDecay(workspace=str(tmp_path))

        result = decay.process_memories([])

        assert result['active'] == []
        assert result['archive'] == []
        assert result['expire'] == []

    def test_log_archive(self, tmp_path):
        """Test logging archived memories"""
        decay = MemoryDecay(workspace=str(tmp_path))

        archived_memories = [
            {'id': 'mem_001', 'activation_level': 0.2},
            {'id': 'mem_002', 'activation_level': 0.1}
        ]

        decay.log_archive(archived_memories)

        # Check log file was created
        log_file = tmp_path / ".claw-mem" / "decay_archive.log"
        assert log_file.exists()

        # Check log content
        log_content = log_file.read_text()
        assert "mem_001" in log_content
        assert "mem_002" in log_content
        assert "Archive Log:" in log_content

    def test_log_archive_empty(self, tmp_path):
        """Test logging with no archived memories"""
        decay = MemoryDecay(workspace=str(tmp_path))

        decay.log_archive([])

        # Should not create log file for empty list
        log_file = tmp_path / ".claw-mem" / "decay_archive.log"
        # File might not exist or be empty
        if log_file.exists():
            content = log_file.read_text()
            # Should not have entries
            assert "Archived 0 memories" in content

    def test_decay_constants(self, tmp_path):
        """Test decay constants are correct"""
        decay = MemoryDecay(workspace=str(tmp_path))

        assert decay.decay_constants['episodic'] == 7
        assert decay.decay_constants['semantic'] == 90
        assert decay.decay_constants['procedural'] == 180

    def test_archive_threshold(self, tmp_path):
        """Test archive threshold is correct"""
        decay = MemoryDecay(workspace=str(tmp_path))

        assert decay.ARCHIVE_THRESHOLD == 0.3

    def test_expiry_days(self, tmp_path):
        """Test expiry days are correct"""
        decay = MemoryDecay(workspace=str(tmp_path))

        assert decay.EXPIRY_DAYS['episodic'] == 30
        assert decay.EXPIRY_DAYS['semantic'] is None
        assert decay.EXPIRY_DAYS['procedural'] is None

    def test_calculate_activation_formula(self, tmp_path):
        """Test activation calculation follows formula A(t) = A₀ * exp(-t/τ)"""
        decay = MemoryDecay(workspace=str(tmp_path))

        memory = {
            'memory_type': 'episodic',
            'accessed_at': datetime.now() - timedelta(days=7),  # Exactly half-life
            'activation_level': 1.0
        }

        activation = decay.calculate_activation(memory)

        # At half-life (τ=7), activation = exp(-7/7) = exp(-1) ≈ 0.368
        assert 0.36 < activation < 0.38

    def test_should_archive_threshold(self, tmp_path):
        """Test archive threshold is 0.3"""
        decay = MemoryDecay(workspace=str(tmp_path))

        # Memory with activation just below threshold (after decay)
        memory_below = {
            'memory_type': 'episodic',
            'accessed_at': datetime.now() - timedelta(days=30),
            'activation_level': 0.29
        }

        # Memory with activation well above threshold (after decay)
        # After 5 days: 0.9 * exp(-5/7) ≈ 0.52 > 0.3
        memory_above = {
            'memory_type': 'episodic',
            'accessed_at': datetime.now() - timedelta(days=5),
            'activation_level': 0.9
        }

        assert decay.should_archive(memory_below) is True
        assert decay.should_archive(memory_above) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
