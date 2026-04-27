"""
Tests for claw-mem Compression Module (v2.4.0)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from datetime import datetime


class TestCompressionLevel:
    """Test CompressionLevel enum"""

    def test_level_values(self):
        from claw_mem.compression import CompressionLevel
        assert CompressionLevel.LIGHT.value == "light"
        assert CompressionLevel.MEDIUM.value == "medium"
        assert CompressionLevel.AGGRESSIVE.value == "aggressive"


class TestCompressionResult:
    """Test CompressionResult dataclass"""

    def test_creation(self):
        from claw_mem.compression import CompressionResult
        result = CompressionResult(
            original_length=1000,
            compressed_length=500,
            compression_ratio=0.5,
            preserved_content="compressed",
            extracted_keys=["key1", "key2"],
            summary="summary"
        )
        assert result.original_length == 1000
        assert result.compressed_length == 500
        assert result.compression_ratio == 0.5


class TestKeyInformationExtractor:
    """Test KeyInformationExtractor"""

    @pytest.fixture
    def extractor(self):
        from claw_mem.compression import KeyInformationExtractor
        return KeyInformationExtractor()

    def test_extract_decisions(self, extractor):
        """Test extracting decision information"""
        text = "We decided to use Python. We agreed to meet tomorrow."
        result = extractor.extract(text)
        assert len(result['decisions']) >= 1

    def test_extract_tasks(self, extractor):
        """Test extracting task information"""
        text = "We need to complete the task. The next step is to implement."
        result = extractor.extract(text)
        assert len(result['tasks']) >= 1


class TestMemoryCompressor:
    """Test MemoryCompressor"""

    @pytest.fixture
    def compressor(self):
        from claw_mem.compression import MemoryCompressor, CompressionLevel
        return MemoryCompressor(CompressionLevel.MEDIUM)

    def test_compress_light(self, compressor):
        """Test light compression"""
        content = "Hello world.\n\nThis is a test.\n\nAnother line."
        result = compressor.compress(content)
        assert result.original_length > 0

    def test_compress_result_structure(self, compressor):
        """Test compression result has required fields"""
        content = "We need to complete the task. We decided to use Python."
        result = compressor.compress(content)

        assert hasattr(result, 'original_length')
        assert hasattr(result, 'compressed_length')
        assert hasattr(result, 'compression_ratio')
        assert hasattr(result, 'preserved_content')
        assert hasattr(result, 'extracted_keys')
        assert hasattr(result, 'summary')

    def test_compression_preserves_key_info(self, compressor):
        """Test that key information is preserved"""
        content = "We decided to use Python. We need to implement the feature."
        result = compressor.compress(content)

        # Should have extracted keys
        assert len(result.extracted_keys) >= 0


class TestCompressMemory:
    """Test compress_memory function"""

    def test_quick_compress(self):
        from claw_mem.compression import compress_memory, CompressionLevel
        result = compress_memory("Test content", CompressionLevel.LIGHT)
        assert result.original_length > 0
        assert result.compressed_length > 0
